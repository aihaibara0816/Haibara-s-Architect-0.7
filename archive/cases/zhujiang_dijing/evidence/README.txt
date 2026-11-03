广州珠江帝景苑 HAF V1 / V1_r03

范围：赏湖轩型湖畔住宅代表楼组与园林研究性近似，非整个小区、非测绘模型。
当前 HAF 0.2.0；HAF 0.3 尚未发布。旧中山纪念堂工程未改。

运行（Python 3.12；numpy、Pillow；预览还需 libEGL/libGL）：
  python3 tools/agent.py --case zhujiang_dijing --run NEW_RUN
  python3 cases/zhujiang_dijing/src/validate_case.py --run NEW_RUN
  python3 tools/render_building_case.py --case zhujiang_dijing --run NEW_RUN
  python3 tools/package_building_case.py --case zhujiang_dijing --run NEW_RUN --name Zhujiang_Dijing_HAF_New
  PYTHONPATH=.:support python3 -m unittest discover -s tests -v

参数：cases/zhujiang_dijing/research/parameters.json
代码：cases/zhujiang_dijing/src/build_case.py
反馈：cases/zhujiang_dijing/feedback_template.json
证据：research/image_manifest.json、component_evidence.json、sources.json
历史：runs/V1_r01、V1_r02 为保留试作，不用于最终导入；r01三个失败检查作为负例。
预览：从最终NBT回读，四向为模型坐标（东+X、北-Z），地理朝向未测。

限制：楼栋编号、精确楼间距/总平、背面窗位和真实夜间灯位待核；伪内饰是补全，无完整楼梯/电梯交通。预览无原版材质纹理，水为静态透明示意。Minecraft导入/碰撞/流体/光照待验证。
