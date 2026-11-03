#!/usr/bin/env python3
"""Package a bounded reference-image manifest into an offline HTML report.

Usage:
  python bundle_reference_images.py --report report.html --manifest images.json \
      --output report-offline.html [--assets-dir downloaded-images]

images.json: {"title": "建筑参考", "images": [{"image_id": "img-001",
  "title": "正面", "local_path": "images/front.jpg", "image_url": null,
  "source_page_url": "https://example.org/project", "verification_status":
  "page_visited_large_image_unverified", "selection_status": "candidate",
  "license": null, "photographer": null}]}

Relative local_path values resolve against the manifest directory. Successful
local files are reused before any network request. Download/pixel inspection
never promotes visual verification or licensing status. Original bytes, EXIF,
watermarks and image dimensions remain unchanged. This is a finite reference
bundle, not a crawler, training set builder, or rights clearance system.
"""
from __future__ import annotations

import argparse
import base64
import binascii
from datetime import datetime, timezone
import hashlib
import html
from html.parser import HTMLParser
import io
import json
from pathlib import Path
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
import warnings
import zipfile

from PIL import Image

VERSION = "1.0.0"
MAX_IMAGE_BYTES = 64 * 1024 * 1024
MAX_IMAGES = 40
MAX_TOTAL_BYTES = 256 * 1024 * 1024
FOLDERS = {"selected": "selected", "candidate": "candidates", "design_reference": "design-reference"}
LABELS = {"selected": "已推荐", "candidate": "候选", "design_reference": "设计参考"}
MIME_EXT = {
    "JPEG": ("image/jpeg", ".jpg"), "PNG": ("image/png", ".png"),
    "WEBP": ("image/webp", ".webp"), "GIF": ("image/gif", ".gif"),
    "BMP": ("image/bmp", ".bmp"), "TIFF": ("image/tiff", ".tif"),
    "ICO": ("image/x-icon", ".ico"), "AVIF": ("image/avif", ".avif"),
}
OWN_BLOCK = re.compile(r"<!-- GAFA-BUNDLE-BEGIN:[a-z0-9_-]+ -->.*?<!-- GAFA-BUNDLE-END:[a-z0-9_-]+ -->", re.S)
IMG_TAG = re.compile(r"<img\b(?:[^>\"']|\"[^\"]*\"|'[^']*')*>\s*", re.I)
SRC_ATTR = re.compile(r"(?<![\w:-])src\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)", re.I)
BUNDLE_ID_ATTR = re.compile(r'\s+data-gafa-image-id\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s>]+)', re.I)
RESPONSIVE_ATTR = re.compile(r"\s+(?:srcset|sizes)\s*=\s*(?:\"[^\"]*\"|'[^']*'|[^\s>]+)", re.I)


def own_block(name: str, markup: str) -> str:
    return f"<!-- GAFA-BUNDLE-BEGIN:{name} -->{markup}<!-- GAFA-BUNDLE-END:{name} -->"


def escape(value) -> str:
    return html.escape(str(value), quote=True)


def safe_stem(value: str, default: str = "image") -> str:
    text = unicodedata.normalize("NFKC", str(value))
    text = re.sub(r"[^\w\u3400-\u9fff-]+", "-", text, flags=re.UNICODE).strip("-._")
    text = text[:90] or default
    # Windows extraction must not produce device names such as CON.jpg.
    if re.fullmatch(r"(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", text, re.I):
        text = "image-" + text
    return text


def safe_url(value) -> str | None:
    if not isinstance(value, str):
        return None
    p = urllib.parse.urlsplit(value)
    return value if p.scheme.lower() in ("http", "https") and p.hostname and not p.username and not p.password else None


def source_link(value, label="原始来源页") -> str:
    url = safe_url(value)
    return f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer">{escape(label)}</a>' if url else "来源页未提供"


def read_limited(path: Path) -> bytes:
    if path.stat().st_size > MAX_IMAGE_BYTES:
        raise ValueError("本地图片超过 64 MiB 单图限制")
    return path.read_bytes()


def fetch_image(url: str, timeout: float) -> tuple[bytes, dict]:
    if not safe_url(url):
        raise ValueError("image_url 必须是无账户凭证的公开 HTTP(S) 图片地址")
    request = urllib.request.Request(url, headers={"User-Agent": "GAFAcraftReferenceBundler/1.0", "Accept": "image/*"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        final_url = response.geturl()
        if not safe_url(final_url):
            raise ValueError("重定向目标不是公开 HTTP(S) 地址")
        content_type = response.headers.get_content_type()
        if content_type in ("text/html", "application/xhtml+xml"):
            raise ValueError("返回的是网页或登录页，不是图片；未继续访问")
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_IMAGE_BYTES:
            raise ValueError("远程图片超过 64 MiB 单图限制")
        data = response.read(MAX_IMAGE_BYTES + 1)
        if len(data) > MAX_IMAGE_BYTES:
            raise ValueError("远程图片超过 64 MiB 单图限制")
        return data, {"resolved_image_url": final_url, "http_content_type": content_type, "http_status": response.status}


def inspect_image(data: bytes) -> dict:
    if not data:
        raise ValueError("图片文件为空")
    with warnings.catch_warnings():
        warnings.simplefilter("error", Image.DecompressionBombWarning)
        with Image.open(io.BytesIO(data)) as picture:
            fmt = picture.format
            width, height = picture.size
            picture.verify()
        if fmt not in MIME_EXT:
            raise ValueError(f"不支持的图片格式：{fmt}")
    mime, extension = MIME_EXT[fmt]
    return {"mime_type": mime, "extension": extension, "pixel_width": width,
            "pixel_height": height, "byte_size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(), "image_format": fmt}


class ImgAttributes(HTMLParser):
    def __init__(self, tag: str):
        super().__init__(convert_charrefs=True)
        self.attrs = {}
        self.feed(tag)

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "img":
            self.attrs = dict(attrs)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


def data_uri(data: bytes, mime: str) -> str:
    return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")


def data_digest(src: str) -> str | None:
    if not src.lower().startswith("data:image/") or "," not in src:
        return None
    header, payload = src.split(",", 1)
    try:
        data = base64.b64decode(re.sub(r"\s+", "", payload), validate=True) if ";base64" in header.lower() else urllib.parse.unquote_to_bytes(payload)
        return hashlib.sha256(data).hexdigest()
    except (ValueError, binascii.Error):
        return None


def collect(manifest: dict, manifest_path: Path, assets_dir: Path, timeout: float) -> tuple[list[dict], dict[int, bytes]]:
    images = manifest.get("images")
    if not isinstance(images, list):
        raise ValueError("manifest.images 必须是数组")
    if len(images) > MAX_IMAGES:
        raise ValueError(f"本工具只处理有限参考图，每次最多 {MAX_IMAGES} 张")
    assets_dir.mkdir(parents=True, exist_ok=True)
    records, raw = [], {}
    seen_ids, used_names = set(), set()
    total_bytes = 0
    for index, item in enumerate(images):
        if not isinstance(item, dict):
            item = {"image_id": None, "invalid_manifest_item": item}
        record = dict(item)
        record.update({"download_status": "failed", "included_in_bundle": False,
                       "visual_verification_automatically_changed": False})
        record.setdefault("verification_status", None)
        record.setdefault("license", None)
        record.setdefault("photographer", None)
        records.append(record)
        try:
            image_id = item.get("image_id")
            if not isinstance(image_id, str) or not image_id.strip():
                raise ValueError("缺少非空 image_id")
            if image_id in seen_ids:
                raise ValueError("image_id 重复")
            seen_ids.add(image_id)
            selection = item.get("selection_status", "candidate")
            if selection not in FOLDERS:
                raise ValueError("selection_status 只能是 selected、candidate 或 design_reference")
            record["selection_status"] = selection
            local_value = item.get("local_path")
            data = None
            if local_value:
                local = Path(local_value).expanduser()
                if not local.is_absolute():
                    local = manifest_path.parent / local
                if local.is_file():
                    data = read_limited(local)
                    record.update({"acquisition_method": "reused_local_file", "input_local_path": str(local.resolve())})
                else:
                    record["local_path_issue"] = "本地文件不存在或不是普通文件"
            if data is None:
                if not item.get("image_url"):
                    raise ValueError("没有可用本地文件，也没有明确的 image_url；未推测原图地址")
                data, response_meta = fetch_image(item["image_url"], timeout)
                record.update(response_meta)
                record["acquisition_method"] = "public_http_download"
            info = inspect_image(data)
            if total_bytes + len(data) > MAX_TOTAL_BYTES:
                raise ValueError("本次图片合计超过 256 MiB 限制")
            filename = safe_stem(image_id) + info["extension"]
            suffix = 2
            while filename.casefold() in used_names:
                filename = f'{safe_stem(image_id)}-{suffix}{info["extension"]}'
                suffix += 1
            used_names.add(filename.casefold())
            destination = assets_dir / filename
            destination.write_bytes(data)
            total_bytes += len(data)
            record.update(info)
            record.update({"download_status": "succeeded", "included_in_bundle": True,
                           "filename": filename, "saved_local_path": str(destination.resolve()),
                           "archive_path": FOLDERS[selection] + "/" + filename,
                           "byte_integrity": "original_bytes_preserved", "download_error": None})
            raw[index] = data
        except Exception as exc:
            if isinstance(exc, urllib.error.HTTPError):
                record["http_status"] = exc.code
                record["download_error"] = f"HTTP {exc.code}；未绕过访问、登录或付费限制"
            else:
                record["download_error"] = f"{type(exc).__name__}: {str(exc)[:500]}"
    return records, raw



# Only public provenance and technical image metadata belong in the user's ZIP.
# Local workspace locations and raw exception messages remain in the sidecar.
PUBLIC_IMAGE_FIELDS = (
    "image_id", "title", "image_url", "resolved_image_url", "source_page_url",
    "verification_status", "selection_status", "license", "photographer",
    "media_type", "view_direction", "view_type", "covered_components",
    "quality_limitations", "copyright_status", "collected_at", "accessed_at",
    "download_status", "included_in_bundle", "acquisition_method",
    "visual_verification_automatically_changed", "http_status", "http_content_type",
    "mime_type", "extension", "pixel_width", "pixel_height", "byte_size",
    "sha256", "image_format", "filename", "archive_path", "byte_integrity",
)


def public_download_error(record: dict) -> str | None:
    """Explain failures without disclosing local paths or arbitrary exceptions."""
    if record.get("included_in_bundle"):
        return None
    if isinstance(record.get("http_status"), int):
        return f'HTTP {record["http_status"]}；未绕过访问、登录或付费限制'
    error = str(record.get("download_error") or "")
    kind, _, detail = error.partition(": ")
    # These messages are fixed by this script; none interpolate a filesystem path.
    safe_messages = (
        "本地图片超过", "远程图片超过", "本次图片合计超过", "图片文件为空",
        "不支持的图片格式：", "没有可用本地文件，也没有明确的 image_url",
        "缺少非空 image_id", "image_id 重复", "selection_status 只能是",
        "image_url 必须是", "重定向目标不是公开 HTTP(S) 地址",
        "返回的是网页或登录页，不是图片",
    )
    if kind == "ValueError" and detail.startswith(safe_messages):
        return detail
    public_by_kind = {
        "UnidentifiedImageError": "文件不是可识别的图片，可能是网页、登录页或无效文件",
        "FileNotFoundError": "本地图片文件不存在，未收录",
        "PermissionError": "本地图片文件读取或保存受限，未收录",
        "TimeoutError": "图片请求超时，未收录",
        "URLError": "公开图片地址请求失败，未收录",
        "DecompressionBombError": "图片像素数量超过安全读取限制，未收录",
        "DecompressionBombWarning": "图片像素数量超过安全读取限制，未收录",
        "OSError": "图片文件读取、解码或保存失败，未收录",
    }
    return public_by_kind.get(kind, "图片下载或文件验证失败，未收录；内部检查记录保留详细原因")


def public_image_record(record: dict) -> dict:
    result = {key: record[key] for key in PUBLIC_IMAGE_FIELDS if key in record}
    result["download_error"] = public_download_error(record)
    return result


def local_reference_key(value: str, base_dir: Path | None = None) -> str | None:
    """Normalize an HTML local reference without opening or discovering files."""
    try:
        parsed = urllib.parse.urlsplit(value)
        if parsed.scheme.lower() == "file":
            if parsed.netloc not in ("", "localhost"):
                return None
        elif parsed.scheme or parsed.netloc:
            return None
        path = Path(urllib.parse.unquote(parsed.path))
        if not path.is_absolute():
            if base_dir is None:
                return None
            path = base_dir / path
        return str(path.resolve())
    except (ValueError, OSError):
        return None


def local_reference_token(value: str) -> str:
    # A non-reversible marker keeps later rebundling possible without publishing paths.
    return "ref-image:local-" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def public_report_gaps(gaps: list[dict]) -> list[dict]:
    result = []
    for gap in gaps:
        public = dict(gap)
        src = public.get("src") or ""
        if not safe_url(src) and not src.startswith("ref-image:"):
            public["src"] = None
            public["reference_kind"] = "unbundled_local_or_non_http_image"
        result.append(public)
    return result


def render(report: str, manifest: dict, records: list[dict], raw: dict[int, bytes], bundle_name: str,
           report_path: Path | None = None) -> tuple[str, list[dict]]:
    # Remove only our own generated blocks; rerunning does not duplicate UI.
    report = OWN_BLOCK.sub("", report)
    by_id = {r.get("image_id"): i for i, r in enumerate(records) if i in raw}
    by_hash = {}
    by_url = {}
    by_local = {}
    by_local_token = {}
    report_dir = report_path.resolve().parent if report_path else None
    for i in raw:
        by_hash.setdefault(records[i]["sha256"], i)
        # Only files explicitly provided and successfully collected by the manifest.
        for path_field in ("input_local_path", "local_path"):
            path_value = records[i].get(path_field)
            if isinstance(path_value, str) and Path(path_value).is_absolute():
                local_key = str(Path(path_value).resolve())
                by_local.setdefault(local_key, i)
                by_local_token.setdefault(local_reference_token(local_key), i)
        for key in ("image_url", "resolved_image_url"):
            if records[i].get(key):
                by_url.setdefault(records[i][key], i)
    seen, gaps = set(), []
    uris = {i: data_uri(data, records[i]["mime_type"]) for i, data in raw.items()}

    def button(i: int) -> str:
        r = records[i]
        caption = (f'{r["image_id"]} · {LABELS[r["selection_status"]]} · '
                   f'{r["pixel_width"]}×{r["pixel_height"]} · 原字节文件 · '
                   f'核验状态：{r.get("verification_status") or "未提供"}')
        return own_block("image-button", f'<span class="gafa-bundle-image-tools"><a class="gafa-bundle-download" href="{uris[i]}" download="{escape(r["filename"])}">下载此图原文件</a><small>{escape(caption)}</small></span>')

    def replace_img(match):
        tag = match.group(0)
        attrs = ImgAttributes(tag).attrs
        src = attrs.get("src") or ""
        index = by_id.get(attrs.get("data-gafa-image-id"))
        if index is not None:
            pass
        elif src.startswith("ref-image:"):
            index = by_id.get(src[len("ref-image:"):])
            if index is None:
                index = by_local_token.get(src)
        elif src in by_url:
            index = by_url[src]
        else:
            digest = data_digest(src)
            if digest:
                index = by_hash.get(digest)
            else:
                local_key = local_reference_key(src, report_dir)
                if local_key:
                    index = by_local.get(local_key)
        if index is not None:
            seen.add(index)
            updated = BUNDLE_ID_ATTR.sub("", RESPONSIVE_ATTR.sub("", tag))
            updated = re.sub(r"\s*/?>", lambda m: ' data-gafa-image-id="' + escape(records[index]["image_id"]) + '"' + m.group(0), updated, count=1)
            replacement = 'src="' + uris[index] + '"'
            updated = SRC_ATTR.sub(lambda m: replacement, updated, count=1)
            return updated + button(index)
        if src.lower().startswith("data:image/"):
            return tag  # Existing offline image not in the manifest is preserved, but not relabeled.
        if src:
            gap = {"src": src, "alt": attrs.get("alt"), "reason": "报告图片未成功纳入本次清单"}
            gaps.append(gap)
            # Do not publish local filesystem paths. A digest can match an explicitly
            # supplied manifest path on a later run, without opening unlisted files.
            is_public_reference = bool(safe_url(src) or src.startswith("ref-image:"))
            stable_reference = src if is_public_reference else local_reference_token(local_reference_key(src, report_dir) or src)
            attrs_markup = f' data-gafa-unbundled-src="{escape(stable_reference)}"'
            display_name = attrs.get("alt") or (src if safe_url(src) else "待补参考图")
            return (f'<span class="gafa-bundle-gap"{attrs_markup}>'
                    f'图片未收录：{escape(display_name)}。'
                    + (source_link(src, "原图片链接") if safe_url(src) else "请将对应图片明确加入清单后重新打包。") + '</span>')
        return tag

    # Recover stable missing-image slots on rerun when the manifest later succeeds.
    gap_pattern = re.compile(r'<span class="gafa-bundle-gap" data-gafa-unbundled-src="([^"]*)">.*?</span>', re.S)
    report = gap_pattern.sub(lambda m: '<img src="' + m.group(1) + '" alt="待补图片">', report)
    # Prefer the embedded fallback img over network-responsive picture sources.
    report = re.sub(r"<picture\b[^>]*>.*?</picture\s*>",
                    lambda m: re.sub(r"<source\b(?:[^>\"']|\"[^\"]*\"|'[^']*')*>", "", m.group(0), flags=re.I),
                    report, flags=re.I | re.S)
    report = IMG_TAG.sub(replace_img, report)
    gallery = []
    for i in raw:
        if i in seen:
            continue
        r = records[i]
        gallery.append(f'<figure><img src="{uris[i]}" alt="{escape(r.get("title") or r["image_id"])}">'
                       + button(i) + f'<figcaption>{escape(r.get("title") or r["image_id"])} · '
                       + source_link(r.get("source_page_url")) + '</figcaption></figure>')

    archive_meta = {
        "bundle_format_version": VERSION,
        "title": manifest.get("title"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": "有限建筑参考素材；不构成训练授权；仅下载不代表已视觉核验",
        "images": [public_image_record(record) for record in records],
        "report_image_gaps": public_report_gaps(gaps),
    }
    if raw:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
            for i, data in raw.items():
                archive.writestr(records[i]["archive_path"], data)
            archive.writestr("sources.json", json.dumps(archive_meta, ensure_ascii=False, indent=2).encode("utf-8"))
        zip_uri = data_uri(buffer.getvalue(), "application/zip")
        download = (f'<a class="gafa-bundle-download" href="{zip_uri}" download="{escape(bundle_name)}-images.zip">'
                    f'下载全部已收录图片（ZIP · {len(raw)} 张）</a>')
    else:
        download = '<strong>尚无可下载的图片文件。已保留缺口和来源信息，补图后可重新打包。</strong>'
    counts = {key: sum(1 for i in raw if records[i]["selection_status"] == key) for key in FOLDERS}
    failures = [r for r in records if not r["included_in_bundle"]]
    notes = (f'已推荐 {counts["selected"]} 张，候选 {counts["candidate"]} 张，设计参考 {counts["design_reference"]} 张；'
             f'未收录 {len(failures)} 张。ZIP 按类别分目录，并附 sources.json。下载与像素检查不改变原核验状态；'
             '公开可访问不等于获得训练或再发布许可。')
    failure_html = ''.join('<li>' + escape(r.get("image_id") or "无编号") + '：' + escape(public_download_error(r))
                           + ' · ' + source_link(r.get("source_page_url")) + '</li>' for r in failures)
    if gaps:
        notes += f' 原报告另有 {len(gaps)} 个未取得的图片位，已标明缺口。'
    top = own_block("top", '<aside class="gafa-bundle-top" aria-label="离线参考图下载">'
                    + '<strong>离线图片资料包</strong><p>' + download + '</p><p>' + escape(notes) + '</p>'
                    + ('<details><summary>未收录图片与原因</summary><ul>' + failure_html + '</ul></details>' if failures else '')
                    + '</aside>')
    styles = own_block("style", '<style>.gafa-bundle-top{margin:20px 0;padding:20px;background:#eef7f8;border:1px solid #bfd7dd;border-radius:10px}.gafa-bundle-download{display:inline-block;margin:5px 8px 5px 0;padding:8px 14px;border-radius:6px;background:#15596c;color:white!important;text-decoration:none}.gafa-bundle-image-tools{display:block;margin:8px 0}.gafa-bundle-image-tools small{display:block;color:#52616b;font:13px/1.6 system-ui}.gafa-bundle-gallery{padding:18px;border:1px solid #cbd5df;margin:24px 0}.gafa-bundle-gallery figure{margin:18px 0}.gafa-bundle-gallery img{max-width:100%;max-height:720px;object-fit:contain}.gafa-bundle-gap{display:block;padding:16px;border:1px dashed #a87e40;background:#fff7e7;overflow-wrap:anywhere}@media print{.gafa-bundle-download{display:none}}</style>')
    if re.search(r'</head\s*>', report, re.I):
        report = re.sub(r'</head\s*>', lambda m: styles + m.group(0), report, count=1, flags=re.I)
    else:
        report = styles + report
    insertion = re.search(r'<main\b[^>]*>', report, re.I) or re.search(r'<body\b[^>]*>', report, re.I)
    if insertion:
        report = report[:insertion.end()] + top + report[insertion.end():]
    else:
        report = top + report
    if gallery:
        gallery_html = own_block("gallery", '<details class="gafa-bundle-gallery"><summary>其他已收录图片（按原分类保留）</summary>' + ''.join(gallery) + '</details>')
        ending = re.search(r'</main\s*>', report, re.I) or re.search(r'</body\s*>', report, re.I)
        if ending:
            report = report[:ending.start()] + gallery_html + report[ending.start():]
        else:
            report += gallery_html
    return report, gaps


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--assets-dir", type=Path)
    parser.add_argument("--timeout", type=float, default=25, help="单张公开图片请求超时秒数，默认 25")
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("manifest 顶层必须是对象")
        report = args.report.read_text(encoding="utf-8")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        assets_dir = args.assets_dir or args.output.with_suffix("").with_name(args.output.stem + "-assets")
        records, raw = collect(manifest, args.manifest.resolve(), assets_dir, args.timeout)
        rendered, gaps = render(report, manifest, records, raw, safe_stem(args.output.stem, "reference"), args.report.resolve())
        args.output.write_text(rendered, encoding="utf-8")
        sidecar = args.output.with_suffix(".assets.json")
        result = {"bundle_format_version": VERSION, "title": manifest.get("title"),
                  "created_at": datetime.now(timezone.utc).isoformat(),
                  "report_path": str(args.output.resolve()), "assets_dir": str(assets_dir.resolve()),
                  "images": records, "report_image_gaps": gaps,
                  "summary": {"requested": len(records), "included": len(raw),
                              "failed": len(records) - len(raw), "original_report_image_gaps": len(gaps)}}
        sidecar.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"output": str(args.output), "metadata": str(sidecar), **result["summary"]}, ensure_ascii=False))
        return 0  # Partial success is explicit in the sidecar and visible report.
    except Exception as exc:
        print(f"bundle_reference_images: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
