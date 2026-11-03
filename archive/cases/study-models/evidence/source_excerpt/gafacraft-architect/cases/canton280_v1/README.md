# 广州塔 V1 复现修补

这是旧V1适配器的副本，未生成SU V2。generation_parameters.json现在是主要轮廓/格构/核心/天线参数输入，case_parameters.json保留旧研究说明。部分场地、塔冠、材料/展示与测试常量仍为280格专用；不是完整通用参数接口，不支持随意改变总高。默认参数经内存生成指纹回归后使用。

未运行新塔楼渲染或导出NBT。旧源码/图片/完整参考字节保留在原GAFAcraft_Canton280_Whitebox.zip。verify_references.py接受原包Canton280根目录，以现存URL清单和哈希验证13张原图，无需缺失的architect_page.html或重新联网。将来重新抓取需单独设计受控入口，旧collect_refs.py不作为可运行入口。
