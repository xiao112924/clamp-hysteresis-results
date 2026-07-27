# Clamp Engineering Skill Library

本仓库整理与夹具、橡胶接触、滞回曲线和实验对比相关的个人 Codex Skill。

## 分类

| 分类 | Skill | 用途 |
|---|---|---|
| ANSYS建模 | `ansys-displacement-assembly-common-node` | 位移装配、UPGEOM、界面共节点、约束恢复和循环加载验证 |
| 滞回后处理 | `process-ansys-hysteresis-drift` | 位移漂移处理、自由截距刚度拟合、中文滞回曲线输出 |
| 工程绘图 | `plot-engineering-curves` | 根据表达式或工程数据绘制中文曲线并导出CSV |
| 数据匹配 | `match-matlab-simulation-data` | 将MATLAB实验曲线与仿真工况CSV逐点匹配并汇总误差 |

## 目录

```text
skills/
  ansys-modeling/
  postprocessing/
  visualization/
  data-integration/
```

每个 Skill 保持标准结构：

```text
skill-name/
  SKILL.md
  agents/openai.yaml
  scripts/           # 仅在需要确定性代码时存在
```

## 使用

将所需 Skill 目录复制到个人 Codex Skill 根目录后重新启动或刷新 Codex。请保持 Skill 文件夹名称不变。

## 验证

- 四个 Skill 均通过 `quick_validate.py` 结构检查。
- `process-ansys-hysteresis-drift` 使用九点力-位移样本验证三种位移处理和自由截距拟合。
- `plot-engineering-curves` 使用正弦压力表达式验证中文PNG与UTF-8 BOM CSV输出。
- `match-matlab-simulation-data` 使用合成MATLAB向量和仿真CSV验证逐点匹配及汇总输出。

## 数据边界

本仓库只保存可复用 Skill 代码，不保存用户仿真模型、实验原始数据、ANSYS RST/DB/CDB、求解器缓存、个人路径或凭据。

