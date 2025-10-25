from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import jieba
import numpy as np
from difflib import SequenceMatcher
import re
import unittest
from sklearn.preprocessing import normalize
from model import User
from datetime import datetime

# 初始化预训练模型（首次运行会自动下载约1.2GB模型文件）
# model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
majors_dict = {
    "计算机科学与技术": "计算机类，学习编程、算法、数据结构、计算机网络、数据库等课程，培养软件开发能力。",
    "计算机科学与技术(嵌入式培养)": "计算机类🌐（校企合作），在编程、算法、数据库基础上强化企业级项目实战，培养全栈开发与云计算部署能力。",
    "电子信息工程": "电子信息类，学习电路设计、嵌入式系统、信号处理、通信原理等课程，培养硬件开发能力。",
    "临床医学": "医学类，学习解剖学、病理学、药理学、内科学、外科学等课程，培养临床诊疗能力。",
    "化学工程与工艺": "化工类，学习化工原理、化学反应工程、化工分离工程、传递过程等课程，培养化工工艺设计能力。",
    "土木工程": "土建类，学习结构力学、工程材料、土木工程施工技术、建筑结构设计等课程，培养工程设计与施工管理能力。",
    "生物技术": "生物科学类，学习分子生物学、基因工程、生物化学、细胞培养技术等课程，培养生物实验与研发能力。",
    "材料科学与工程": "材料类，学习材料物理、材料化学、纳米材料、材料加工工艺等课程，培养新材料研发能力。",
    "电气工程及其自动化": "电气类，学习电力系统分析、电机与拖动、PLC控制技术、高电压工程等课程，培养电力系统设计与运维能力。",
    "自动化": "自动化类，计算机类，学习控制理论、传感器技术、工业机器人、过程控制系统等课程，培养工业自动化解决方案能力。",
    "新闻学": "新闻传播类，学习新闻采访、编辑学、传播学理论、新媒体运营等课程，培养新闻采编与内容创作能力。",
    "国际关系": "政治学类，学习国际政治、外交学、全球治理、跨文化沟通等课程，培养国际事务分析与政策研究能力。",
    "药学": "医药类，学习药物化学、药理学、药剂学、药品质量管理等课程，培养药物研发与药品监管能力。",
    "护理学": "医学类，学习基础护理学、内科护理、外科护理、急重症护理等课程，培养临床护理与健康管理能力。",
    "教育学": "教育类，学习教育心理学、课程设计、教育统计学、教育技术学等课程，培养教学设计与教育管理能力。",
    "统计学": "理学类，学习概率论、数理统计、数据可视化、机器学习基础等课程，培养数据分析与建模能力。",
    "物流管理": "管理类，学习供应链管理、仓储与配送、物流系统规划、国际物流等课程，培养供应链优化能力。",
    "食品科学与工程": "食品类，学习食品化学、食品微生物学、食品加工工艺、食品安全检测等课程，培养食品研发与质量控制能力。",
    "艺术设计": "艺术类，学习平面设计、三维建模、品牌视觉设计、用户体验设计等课程，培养创意设计与数字化表达能力。",
    "软件工程": "计算机类，学习软件架构设计、软件测试、DevOps、云计算等课程，培养全栈开发与项目管理能力。",
    "软件工程(嵌入式培养)": "计算机类🌐（产教融合），通过软件测试、DevOps、微服务架构等企业化实训，培养敏捷开发与运维一体化能力。",
    "网络工程": "计算机类，学习网络规划与设计、防火墙与路由器配置、TCP/IP协议、Linux网络管理、综合布线技术等课程，培养网络系统设计、部署与维护能力。",
    "数据科学与大数据技术": "计算机类，学习数据挖掘、分布式计算、Python编程、商业智能等课程，培养大数据分析与决策支持能力。",
    "电子科学与技术": "电子信息类，学习半导体物理、光电子技术、集成电路设计、电磁场与微波技术等课程，培养电子器件研发与系统集成能力。",
    "人工智能": "交叉学科类，学习机器学习、深度学习、自然语言处理、计算机视觉等课程，培养AI算法开发能力。",
    "物联网工程": "计算机类，学习传感器技术、嵌入式系统、RFID原理、物联网通信协议、云计算与边缘计算等课程，培养物联网终端设备开发与系统集成能力。",
    "航空航天工程": "航空航天类，学习空气动力学、飞行器结构设计、航天器控制、火箭发动机原理等课程，培养飞行器研发能力。",
    "能源与动力工程": "能源类，学习热力学、流体力学、新能源技术、能源系统优化等课程，培养能源设备设计与节能减排能力。",
    "信息安全": "计算机类，学习密码学、网络攻防技术、漏洞挖掘、区块链原理等课程，培养网络信息安全防护能力。",
    "智能科学与技术": "交叉学科类，学习模式识别、智能信息处理、机器人学、脑科学与认知科学基础等课程，培养智能系统设计与优化能力。",
    "人力资源管理": "管理类，学习组织行为学、薪酬管理、招聘与培训、劳动法等课程，培养人才管理与组织发展能力。",
    "翻译": "文学类，学习口译技巧、笔译实践、跨文化交际、专业领域翻译等课程，培养多语种语言服务能力。",
    "会计学": "管理类，学习财务会计、管理会计、税法、审计学等课程，培养财务核算与风险控制能力。",
    "动画": "艺术类，学习角色设计、三维动画制作、影视特效、游戏引擎应用等课程，培养数字内容创作能力。",
    "酒店管理": "管理类，学习酒店运营管理、客户服务、旅游市场营销、宴会策划等课程，培养酒店服务与品牌运营能力。",
    "农业科学": "农学类，学习作物栽培学、土壤肥料学、农业生态学、农业经济管理等课程，培养现代农业技术推广能力。",
    "地质学": "理学类，学习矿物岩石学、构造地质学、地质灾害防治、遥感地质学等课程，培养地质勘探与资源评估能力。",
    "海洋科学": "理学类，学习海洋生物学、物理海洋学、海洋化学、海洋资源开发等课程，培养海洋环境监测与保护能力。",
    "社会学": "法学类，学习社会调查方法、社会统计学、城乡社会学、社会政策分析等课程，培养社会问题研究与政策建议能力。",
    "历史学": "历史学类，学习中国通史、世界通史、考古学基础、文化遗产保护等课程，培养历史研究与文化传播能力。",
    "电子商务": "管理类，学习网络营销、电子支付、跨境电商、用户体验设计等课程，培养电商平台运营与数字化营销能力。",
    "数字媒体技术": "计算机类，学习虚拟现实技术、交互设计、影视后期制作、游戏开发等课程，培养数字内容生产与技术整合能力。",
    "生物医学工程": "生物工程类，学习医学成像技术、生物材料、医疗仪器设计、生物信号处理等课程，培养医疗器械研发能力。",
    "城乡规划": "工学类，学习城市规划原理、GIS空间分析、土地利用规划、景观设计等课程，培养城市可持续发展规划能力。",
    "音乐表演": "艺术类，学习声乐/器乐技巧、音乐理论、舞台表演、音乐教育等课程，培养艺术表现与教学能力。",
    "体育教育": "教育类，学习运动训练学、体育心理学、运动损伤防护、体育赛事管理等课程，培养体育教学与健身指导能力。",
    "旅游管理": "管理类，学习旅游规划与开发、景区管理、旅游消费者行为、导游实务等课程，培养旅游产品设计与目的地管理能力。",
    "通信工程": "电子信息类，学习数字信号处理、移动通信、光纤通信、5G网络架构等课程，培养通信系统设计与优化能力。",
    "微电子科学与工程": "电子信息类，学习半导体器件物理、芯片制造工艺、VLSI设计、封装测试技术等课程，培养集成电路制造与工艺开发能力。",
    "集成电路设计与集成系统": "电子信息类，学习模拟集成电路设计、数字系统设计、EDA工具应用、SoC开发等课程，培养芯片级系统设计能力。",
    "测控技术与仪器": "自动化类，学习传感器技术、自动检测系统、精密仪器设计、智能仪器开发等课程，培养工业测控系统设计能力。",
    "机器人工程": "自动化类，学习机器人运动学、机器视觉、伺服控制、ROS系统开发等课程，培养智能机器人系统集成能力。",
    "机械电子工程": "机电类，学习机电一体化设计、PLC控制、液压与气动技术、工业机器人应用等课程，培养智能制造装备开发能力。",
    "储能科学与工程": "能源类，学习电化学储能、热力储能、能源系统优化、电池管理系统设计等课程，培养新能源存储技术研发能力。",
    "轨道交通信号与控制": "交通类，学习列车运行控制、轨道交通通信、信号系统设计、CBTC技术等课程，培养轨道交通智能化管控能力。",
    "车辆工程": "机械类，学习汽车构造、车辆动力学、新能源汽车技术、智能网联汽车系统等课程，培养汽车设计与研发能力。",
    "交通运输": "交通类，学习交通规划、运输经济学、智能交通系统、物流运输管理等课程，培养综合运输系统优化能力。",
    "环境科学与工程": "环境类，学习水污染控制、大气污染防治、固体废物处理、环境影响评价等课程，培养环境治理工程技术能力。",
    "应用化学": "化学类，学习精细化学品合成、分析检测技术、化工过程模拟、材料化学等课程，培养化学应用技术创新能力。",
    "大气科学": "理学类，学习大气物理学、天气学原理、气候数值模拟、气象卫星遥感等课程，培养气象预报与气候分析能力。",
    "地理信息科学": "理学类，学习GIS原理、空间数据库、遥感图像处理、三维地理建模等课程，培养空间数据分析与可视化能力。",
    "遥感科学与技术": "理学类，学习遥感物理基础、数字图像处理、微波遥感、遥感地学分析等课程，培养遥感信息提取与行业应用能力。",
    "测绘工程": "理学类，学习工程测量、卫星定位技术、摄影测量学、变形监测分析等课程，培养空间地理信息采集与处理能力。",
    "安全工程": "工程类，学习系统安全工程、火灾防治技术、风险分析与评估、应急管理等课程，培养安全生产管理与事故防控能力。",
    "金融工程": "经济类，学习金融衍生品定价、量化投资、金融风险管理、Python金融分析等课程，培养金融产品设计与量化分析能力。",
    "国际经济与贸易": "经济类，学习国际贸易实务、国际商法、跨境电商、WTO规则等课程，培养跨境商务运作与贸易谈判能力。",
    "财务管理": "管理类，学习财务报表分析、资本运营、投资学、财务大数据分析等课程，培养企业投融资决策与风险管理能力。",
    "市场营销": "管理类，学习消费者行为学、品牌管理、数字营销、市场调研等课程，培养全渠道营销策划与执行能力。",
    "信息管理与信息系统": "管理类，学习ERP原理、商务智能、信息系统分析与设计、IT项目管理等课程，培养企业数字化转型升级能力。",
    "应急管理": "管理类，学习危机管理、应急预案编制、灾害风险评估、公共安全技术等课程，培养突发事件应对与应急指挥能力。",
    "数字媒体艺术": "艺术类，学习三维动画、交互设计、虚拟现实艺术、新媒体装置创作等课程，培养数字内容创意与跨媒体表达能力。",
    "艺术与科技": "艺术类，学习科技艺术创作、沉浸式空间设计、数据可视化艺术、智能硬件交互等课程，培养跨界融合创新设计能力。",
    "数字媒体艺术（中外合作办学）": "艺术类🌐（国际合作），引入国际数字艺术课程体系，培养具有全球视野的交互媒体设计与跨文化创作能力。",
    "国际经济与贸易（四年制全英文授课）": "经济类🌐（全英文），采用英文原版教材，强化国际商务谈判与跨境电商运营能力，对接国际经贸规则。",
    "计算机科学与技术（四年制全英文授课）": "计算机类🌐（全英文），全程英语教学，侧重人工智能与大数据前沿技术，培养国际化软件开发能力。",
    "电子信息工程（四年制全英文授课）": "电子信息类🌐（全英文），英文讲授嵌入式系统与智能硬件开发，培养国际电子设计竞赛能力。",
    "国际经济与贸易（两年制中文授课）": "经济类🌐（专升本），聚焦国际贸易实务与跨境电商运营，强化职业资格认证衔接。",
    "计算机科学与技术（两年制中文授课）": "计算机类🌐（专升本），深化全栈开发与云计算技术，对接IT行业职业认证体系。",
    "数字媒体艺术（两年制中文授课）": "艺术类🌐（专升本），加强三维动画与交互设计实战训练，衔接数字内容产业岗位需求。"
}
positions_dict = {
    "Java开发工程师": "计算机类,负责Java后端服务开发，熟悉Spring Boot/微服务架构，掌握分布式系统设计。",
    "前端开发工程师": "计算机类,使用HTML/CSS/JavaScript构建用户界面，熟悉Vue.js/React框架及前端工程化。",
    "移动开发工程师（Android/iOS）": "计算机类,开发Android（Kotlin/Java）或iOS（Swift）应用，熟悉跨平台框架如Flutter。",
    "游戏开发工程师": "计算机类,使用Unity/Unreal Engine开发游戏逻辑，熟悉C#/C++及物理引擎优化。",
    "区块链开发工程师": "计算机类,基于Solidity开发智能合约，熟悉以太坊/Hyperledger等区块链平台架构。",
    "云计算工程师": "计算机类,部署维护AWS/Aliyun云服务，熟悉Docker/Kubernetes容器化及自动化运维。",
    "大数据开发工程师": "计算机类,构建Hadoop/Spark数据处理管道，熟悉Hive/HBase等大数据组件调优。",
    "测试开发工程师": "计算机类,设计自动化测试框架，使用Selenium/JUnit编写测试用例，提升代码覆盖率。",
    "运维工程师": "计算机类,负责服务器监控与故障排查，熟悉Linux系统及Ansible/Prometheus运维工具链。",
    "网络安全工程师": "计算机类,实施渗透测试与漏洞修复，熟悉WAF配置及SOC安全事件响应流程。",
    "物联网开发工程师": "计算机类,开发物联网设备通信协议，熟悉MQTT/CoAP及边缘计算框架应用。",
    "AR/VR开发工程师": "计算机类,开发增强现实/虚拟现实应用，熟悉Unity3D引擎及SLAM空间定位技术。",
    "自然语言处理工程师": "计算机类,构建文本分类/机器翻译模型，熟悉Transformer架构及Hugging Face生态。",
    "推荐系统工程师": "计算机类,设计个性化推荐算法，熟悉协同过滤/深度学习推荐模型落地。",
    "音视频开发工程师": "计算机类,优化音视频编解码性能，熟悉FFmpeg/WebRTC及实时传输协议（RTP/RTSP）。",
    "低代码平台开发工程师": "计算机类,开发可视化编程工具，熟悉DSL设计及元数据驱动开发模式。",
    "量化开发工程师": "计算机类,搭建金融量化交易系统，熟悉Python/C++高频交易策略实现。",
    "边缘计算工程师": "计算机类,优化边缘节点资源调度，熟悉KubeEdge/OpenYurt等边缘计算框架。",
    "RPA开发工程师": "计算机类,设计流程自动化机器人，熟悉UiPath/Automation Anywhere企业级部署。",
    "元宇宙应用开发工程师": "计算机类,开发虚拟场景交互功能，熟悉Web3.js及数字资产（NFT）合约集成。",
    "Python开发工程师": "计算机类,负责Python后端开发，熟悉Django/Flask框架，有数据库设计和优化经验。",
    "嵌入式开发工程师": "计算机类,负责嵌入式系统开发，熟悉C语言、单片机、硬件调试。",
    "医学影像助理": "医学类,协助医学影像诊断，熟悉CT、MRI等设备的操作和病例分析。",
    "化工工艺工程师助理": "化工类,协助工艺流程设计与优化，熟悉Aspen等化工模拟软件，参与生产现场技术支持。",
    "结构设计助理": "建筑类,协助建筑结构设计与图纸绘制，熟悉AutoCAD和BIM工具，参与施工图审核。",
    "生物实验助理": "生物类,协助分子生物学实验操作，掌握PCR、电泳等基础技术，参与实验室数据记录与分析。",
    "材料研发工程师助理": "材料类,参与新型材料性能测试与改进，熟悉SEM/XRD等材料表征仪器操作。",
    "电力系统工程师助理": "能源类,协助变电站设计或电力设备调试，熟悉MATLAB/Simulink电力系统仿真。",
    "工业自动化实习生": "机械类/计算机类,参与PLC编程与生产线自动化改造，熟悉西门子/三菱控制系统。",
    "新闻采编实习生": "传媒类,协助新闻稿件撰写与新媒体内容编辑，参与采访策划与热点追踪。",
    "国际事务助理": "国际关系类,协助国际组织文件翻译与政策研究，参与跨文化沟通项目协调。",
    "药剂师助理": "医学类,协助药品调配与处方审核，参与药房库存管理及患者用药指导。",
    "临床护理实习生": "医学类,协助基础护理操作与病历记录，参与病房巡查及健康宣教工作。",
    "教育机构助教": "教育类,协助课程材料准备与学生答疑，参与教学效果评估与课堂管理。",
    "数据分析师实习生": "计算机类,使用Python/SQL进行数据清洗与可视化，协助业务部门生成分析报告。",
    "供应链管理助理": "管理类,协助物流仓储系统优化，参与供应商协调与库存周转率分析。",
    "食品研发助理": "食品类,参与新产品配方试验与感官评测，协助食品安全检测及标准制定。",
    "平面设计实习生": "设计类,使用PS/AI完成海报、LOGO设计，协助品牌视觉方案落地。",
    "全栈开发实习生": "计算机类,参与前后端功能开发，熟悉Vue/React框架及RESTful API设计。",
    "数据挖掘实习生": "计算机类,使用机器学习算法构建用户画像，参与推荐系统模型优化。",
    "机器学习工程师实习生": "计算机类,协助图像识别/NLP模型训练，参与TensorFlow/PyTorch项目开发。",
    "飞行器设计助理": "航空航天类,参与气动外形仿真与结构强度计算，熟悉ANSYS/Fluent等工具。",
    "新能源工程师助理": "能源类,协助光伏/风电项目可行性分析，参与储能系统技术方案设计。",
    "网络安全实习生": "计算机类/电子信息类,参与渗透测试与漏洞修复，熟悉防火墙配置及安全日志分析。",
    "HR实习生": "管理类,协助简历筛选与招聘面试安排，参与员工培训活动组织。",
    "翻译助理": "语言类,完成技术文档/商务合同的笔译任务，协助国际会议交替传译。",
    "审计实习生": "财务类,协助财务凭证抽查与底稿编制，参与企业内控流程评估。",
    "动画制作实习生": "计算机类/艺术类,使用Maya/Blender制作三维动画，参与影视特效合成与渲染。",
    "酒店运营实习生": "旅游类,协助前台接待与客户服务，参与客房管理系统的数据维护。",
    "农业技术推广员": "农业类,参与田间试验与技术示范，协助农户进行种植方案优化。",
    "地质勘探助理": "地质类,协助野外地质调查与样本采集，参与矿产资源评估报告撰写。",
    "海洋监测技术员": "海洋类,参与海水采样与水质分析，协助海洋生态保护项目数据整理。",
    "社会调查员": "社会学类,协助问卷设计与入户访谈，使用SPSS进行社会问题数据分析。",
    "文化遗产保护助理": "历史类,参与文物修复记录与档案管理，协助博物馆展览策划工作。",
    "电商运营助理": "电子商务类,协助商品上架与促销活动策划，参与直播带货脚本撰写。",
    "新媒体运营实习生": "传媒类,负责公众号/短视频平台内容更新，分析用户互动数据并优化策略。",
    "医疗器械研发助理": "医学类,协助医疗设备原型测试，参与注册申报材料准备。",
    "城市规划助理": "建筑类,使用ArcGIS进行用地现状分析，协助编制城市更新方案。",
    "音乐教育助理": "教育类,协助乐器教学与排练组织，参与艺术展演活动策划。",
    "健身教练实习生": "体育类,协助制定个性化训练计划，参与团体课程教学与会员维护。",
    "旅游策划助理": "旅游类,协助设计旅游线路与主题活动，参与景区数字化导览系统开发。",
    "GIS开发工程师": "计算机类,使用ArcGIS/QGIS进行空间数据分析，参与地理信息系统二次开发与地图服务发布。",
    "气象数据分析助理": "气象类,处理卫星云图与气象观测数据，协助构建数值天气预报模型。",
    "环境监测技术员": "环境类,采集水样/大气样本，操作COD分析仪、气相色谱等设备生成检测报告。",
    "化学分析助理": "化学类,使用HPLC/ICP-MS进行物质成分检测，协助实验室质量体系认证。",
    "遥感数据处理助理": "地理类,预处理多光谱/雷达遥感影像，使用ENVI/ERDAS完成土地分类解译。",
    "芯片设计助理": "电子类,参与数字电路前端设计，使用Verilog/VHDL进行FPGA原型验证。",
    "半导体工艺工程师助理": "电子类,协助光刻/刻蚀工艺调试，参与晶圆良率分析与SPC控制。",
    "光电子技术助理": "电子类,测试光纤器件传输特性，协助激光器驱动电路设计与光学系统装调。",
    "储能系统工程师助理": "能源类,搭建电池管理系统(BMS)测试平台，参与储能电站容量配置优化。",
    "汽车测试工程师助理": "机械类,执行NVH测试与ADAS系统路测，使用CANoe分析车辆总线数据。",
    "交通规划助理": "建筑类,使用TransCAD进行交通流量预测，协助公交线网优化方案设计。",
    "应急响应助理": "公共安全类,参与应急预案数字化建模，协助搭建应急指挥信息系统原型。",
    "交互设计实习生": "设计类,使用Figma完成智能硬件交互原型设计，参与用户可用性测试。",
    "数字内容创作实习生": "艺术类,运用UE5引擎制作数字孪生场景，参与虚拟直播技术方案开发。",
    "量化分析实习生": "金融类,构建多因子选股模型，使用Wind/同花顺进行金融数据回测验证。",
    "安全评估助理": "化工类,开展HAZOP分析，使用PHAST软件进行化工装置事故后果模拟。",
    "测绘技术员": "地理类,操作全站仪/三维激光扫描仪，使用CASS软件生成数字化地形图。",
    "跨境电商运营助理": "电子商务类,协助Amazon/Shopify店铺运营，参与多语言商品详情页优化。",
    "国际科研项目助理": "科研类,整理英文技术文档，协助申报材料准备与国际学术会议组织。",
    "IT支持工程师": "计算机类,部署OA系统与网络设备，为中小企业提供信息化升级解决方案。",
    "数字营销专员": "市场营销类,运营独立站与社媒账号，使用Google Analytics优化广告投放ROI。"
}

def extract_category(desc):
    """从专业描述中提取类别（首个逗号前的内容）"""
    if '，' in desc:
        return desc.split('，', 1)[0].strip()
    return ""


def tokenize_category(category):
    """对类别名称进行分词并过滤停用词"""
    words = jieba.cut(category)
    return [w for w in words if w not in stop_words and len(w) > 1]


def calculate_category_bonus(major_desc, position_desc):
    """计算类别匹配的额外加分"""
    # 提取专业类别
    major_category = extract_category(major_desc)
    if not major_category:
        return 0

    # 分词并过滤
    category_keywords = tokenize_category(major_category)
    if not category_keywords:
        return 0

    # 处理岗位描述
    position_tokens = tokenize(position_desc).split()

    # 计算匹配词频
    match_count = sum(1 for kw in category_keywords if kw in position_tokens)

    # 加分规则：每个匹配词加0.1分，最高加0.3分
    return min(match_count * 0.1, 0.3)


def calculate_similarity(text1, text2):
    vectorizer = TfidfVectorizer(tokenizer=tokenize)
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]

    # 添加类别权重加成
    category_bonus = calculate_category_bonus(text1, text2)
    return min(similarity + category_bonus, 1.0)  # 确保不超过1


def match_single_student(student_major, target_position, majors_dict, positions_dict):
    # 模糊匹配岗位名称（原有逻辑保持不变）
    matched_position = find_closest_position(target_position, positions_dict)
    if not matched_position:
        return None, 0.0

    # 获取描述文本
    major_desc = majors_dict.get(student_major, "")
    position_desc = positions_dict.get(matched_position, "")

    if not major_desc or not position_desc:
        raise ValueError("匹配异常")

    # 计算增强后的相似度（已包含类别加成）
    similarity = calculate_similarity(major_desc, position_desc)
    return matched_position, similarity


def match_major_position(majors, positions):
    results = []
    for major_name, major_desc in majors.items():
        for position_name, position_desc in positions.items():
            # 直接使用增强后的相似度计算
            similarity = calculate_similarity(major_desc, position_desc)
            results.append({
                "major": major_name,
                "position": position_name,
                "similarity": round(similarity, 2)
            })
    return sorted(results, key=lambda x: x["similarity"], reverse=True)


def match_single_major_position(major, position, majors_dict, positions_dict):
    results = []
    major_desc = majors_dict.get(major_name)
    position_desc = positions_dict.get(position_name)

    similarity = calculate_similarity(major_desc, position_desc)
    results.append({
        "major": major_name,
        "position": position_name,
        "similarity": round(similarity, 2)
    })
    return sorted(results, key=lambda x: x["similarity"], reverse=True)


def find_closest_position(input_position, positions_dict, threshold=0.5):
    """
    模糊匹配岗位名称
    :param input_position: 用户输入的岗位名称
    :param positions_dict: 岗位字典
    :param threshold: 相似度阈值
    :return: 最匹配的岗位名称
    """
    input_norm = normalize_text(input_position)
    candidates = []

    for position in positions_dict:
        # 双重匹配策略
        ratio = position_similarity(input_norm, normalize_text(position))
        candidates.append((position, ratio))

    # 按相似度排序
    candidates.sort(key=lambda x: x[1], reverse=True)

    if candidates and candidates[0][1] >= threshold:
        return candidates[0][0]
    return None


tech_terms = [
    "Java", "Spring Boot", "MySQL", "微服务", "分布式系统",
    "数据结构与算法", "高并发", "JUnit", "DevOps", "Oracle", "计算机类",
    "医学类", "化工类", "建筑类", "生物类", "材料类", "能源类", "机械类", "传媒类", "国际关系类", "教育类", "管理类", "食品类", "设计类", "语言类",
    "财务类", "艺术类", "旅游类", "农业类", "地质类", "海洋类", "社会学类", "历史类", "电子商务类", "航空航天类", "电子类",  # 原需求中「电子信息类」已合并至此"公共安全类","金融类",
    "地理类", "环境类", "化学类", "市场营销类", "科研类"
]
for term in tech_terms:
    jieba.add_word(term, freq=10000)  # 极高权重确保精准切分

# def tokenize(text):
#     # 清理标点符号和非中文字符
#     text = re.sub(r'[^\u4e00-\u9fa5]', '', text)
#
#     # 精准分词（关闭HMM新词发现）
#     words = jieba.cut(text, cut_all=False, HMM=False)
#
#     # 强制合并技术术语（最终防御）
#     merged = []
#     buffer = ""
#     for word in words:
#         if word in tech_terms:
#             if buffer:
#                 merged.append(buffer)
#                 buffer = ""
#             merged.append(word)
#         else:
#             buffer += word
#     if buffer:
#         merged.append(buffer)
#
#     # 过滤单字（可选）
#     filtered = [w for w in merged if len(w) > 1 or w in tech_terms]
#
#     print("[DEBUG] 最终分词:", filtered)
#     return filtered  # 直接返回词语列表！
user_dict = set()
try:
    with open("words.txt", 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                word = line.split()[0]  # 提取词语部分（忽略词频和词性）
                user_dict.add(word)
except FileNotFoundError:
    print("Warning: words.txt not found, using default user_dict.")


def tokenize(text):
    """分词函数：保留自定义词典中的词，其他拆分成单字"""
    # 文本清洗（去除非字母数字和中文的字符）
    text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
    # 使用 jieba 分词
    words = jieba.lcut(text)
    # 处理未在自定义词典中的词（拆分成单字）
    processed_words = []
    for word in words:
        if word in user_dict:
            processed_words.append(word)
        else:
            processed_words.extend(list(word))  # 拆分成单字
    # 过滤停用词
    processed_words = [word for word in processed_words if word not in stop_words]
    return processed_words


# 停用词过滤（直接嵌入）
stop_words = {"的", "和", "与", "等", "、", "（", "）", "熟悉", "掌握"}


def position_similarity(a, b):
    """计算两个岗位名称的相似度得分"""
    return SequenceMatcher(None, a, b).ratio()


def normalize_text(text):
    """文本标准化处理：统一小写、去除标点、去除空格"""
    text = text.lower()
    text = re.sub(r'[^\w\u4e00-\u9fff]', '', text)  # 保留中文和字母数字
    return text.strip()


stop_words = {"的", "和", "与", "等", "、", "（", "）", "熟悉", "掌握"}


def match_single_major_position(major, position, majors_dict, positions_dict):
    results = []
    major_desc = majors_dict.get(major)
    position_desc = positions_dict.get(position)

    similarity = calculate_similarity(major_desc, position_desc)
    results.append({
        "major": major_name,
        "position": position_name,
        "similarity": round(similarity, 2)
    })
    return sorted(results, key=lambda x: x["similarity"], reverse=True)


def calculate_similarity(text1, text2, boost_suffix='类', boost_factor=15.0):
    # 初始化TF-IDF向量化器（禁用默认L2归一化）
    vectorizer = TfidfVectorizer(
        tokenizer=tokenize,  # 使用改造后的分词器
        token_pattern=None,  # 禁用默认的正则匹配
        lowercase=False,  # 禁用小写转换
        # 明确指定按词语分析
        min_df=1,  # 允许所有词语作为特征
        stop_words=stop_words
    )
    tfidf_matrix = vectorizer.fit_transform([text1, text2])
    # 获取特征名称
    feature_names = vectorizer.get_feature_names_out()
    print('特征名称', feature_names)

    boost_indices = [
        i for i, word in enumerate(feature_names)
        if word.endswith(boost_suffix)  # 关键修改：检查词是否以 boost_suffix 结尾
    ]

    # 创建权重数组并应用
    if boost_indices:
        weights = np.ones(len(feature_names))
        weights[boost_indices] = boost_factor
        tfidf_matrix = tfidf_matrix.multiply(weights)

    # 进行L2归一化
    tfidf_matrix = normalize(tfidf_matrix, norm='l2')

    # 获取两个文档的非零特征索引
    doc1_indices = set(tfidf_matrix[0].nonzero()[1])
    doc2_indices = set(tfidf_matrix[1].nonzero()[1])

    # 找到共同出现的特征
    common_indices = doc1_indices & doc2_indices

    # 筛选出被加权的共同特征
    boosted_common = [feature_names[i] for i in common_indices if i in boost_indices]

    # 打印匹配到的高权重词条
    if boosted_common:
        print("匹配到的高权重词条：", ", ".join(boosted_common))
    else:
        print("未匹配到高权重词条")
    return cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]


if __name__ == "__main__":
   print(datetime.now())

