# 场景与架构元素：草稿态、审批入库与还原 — 软件架构设计

## 1. 业务需求简述

- **草稿态**：用户对「场景」和「架构元素」的修改先进入草稿，不直接改写已发布数据。
- **审批入库**：用户通过审批接口确认后，草稿内容一次性写入正式库（已发布数据）。
- **还原修改**：用户可放弃草稿，将当前版本恢复为「上次审批后的状态」。

## 2. 设计原则

- **版本粒度**：以「版本」为草稿边界，一个版本下有一份已发布数据 + 一份草稿数据；列表/详情可按「只看已发布」或「只看草稿」查询。
- **一致性**：场景与架构元素存在关联（如场景流程引用架构元素），草稿的审批/还原以版本为单位整体处理，避免出现「场景引用了未审批的架构元素」等不一致。
- **可还原**：已发布数据仅在「审批」时被覆盖；还原只丢弃草稿，不动已发布数据。

## 3. 推荐架构：双区存储（已发布 + 草稿表）

### 3.1 数据模型

- **已发布区**：沿用现有表，视为「已审批」的正式数据。  
  - 场景：`scene_record`、`scene_flow`、`scene_flow_element`  
  - 架构：`arch_overview`、`arch_element`、`arch_dependency`，以及构建/部署/接口/决策等现有表（若需纳入草稿可同样加草稿表）
- **草稿区**：为需要支持草稿的实体增加「草稿表」，与主表结构一致，通过 `version_id`（+ 可选 `draft_owner_id`）限定归属。

建议先对「场景 + 逻辑架构」做了草稿支持，草稿表命名与主表一一对应，例如：

| 已发布表（现有） | 草稿表（新增） |
|------------------|----------------|
| `scene_record` | `scene_record_draft` |
| `scene_flow` | `scene_flow_draft` |
| `scene_flow_element` | `scene_flow_element_draft` |
| `arch_overview` | `arch_overview_draft` |
| `arch_element` | `arch_element_draft` |
| `arch_dependency` | `arch_dependency_draft` |

草稿表字段与主表一致，主键仍用 UUID；外键指向规则：

- 草稿表之间引用用「草稿表主键」（如 `scene_flow_draft.scene_id` → `scene_record_draft.id`）。
- 与「仅存在于已发布表」的实体（如 `version_record`）仍用原表主键（如 `version_id` → `version_record.id`）。
- **场景流程关联架构元素**：`scene_flow_element_draft.element_id` 在草稿阶段可指向 `arch_element_draft.id`；审批时先写架构再写场景，保证 ID 一致写入主表，或审批前校验「引用的架构元素均在本次草稿内或已发布表中存在」。

### 3.2 状态与归属（可选）

- 若不做多人在线编辑，可每版本仅保留一份草稿，不落库「谁在编辑」。
- 若需支持「多人协作 / 锁定」，可在草稿表增加 `draft_owner_id`、`draft_started_at`，列表/保存时按 `version_id + draft_owner_id` 过滤；审批/还原时可设计为「仅草稿归属者或管理员可操作」。

## 4. 核心流程

### 4.1 保存草稿

- 用户对场景/架构的增删改，**只写草稿表**（或先删后插，保证草稿表是该版本在该用户下的唯一副本）。
- 若希望「编辑时自动进草稿」，则现有创建/更新接口改为：
  - 先查/建该版本草稿行（或整份副本），再在草稿表上做 create/update/delete。
- 前端或接口层可约定：同一版本下「有草稿则展示草稿，否则展示已发布」。

### 4.2 审批入库

- **入口**：例如 `POST /api/v1/versions/{version_id}/draft/approve`（可带 `user_id` 做权限/审计）。
- **逻辑**（建议在单一事务中执行）：
  1. 按依赖顺序，将草稿表数据合并到已发布表：  
     架构（overview → element → dependency）→ 场景（scene → flow → flow_element）。  
  2. 合并策略：  
     - **全量覆盖**：删除该版本在主表中已有数据，再将草稿表整批插入主表（需处理外键、顺序）；或  
     - **按主键 upsert**：草稿与主表主键一致时，用草稿内容 overwrite 主表对应行；主表有而草稿无则保留或按产品约定删除。  
  3. 清空该版本下所有草稿表（或标记草稿为已审批，视是否保留历史而定）。

### 4.3 还原修改

- **入口**：例如 `POST /api/v1/versions/{version_id}/draft/revert`。
- **逻辑**：删除该版本下所有草稿表中的数据（及可选的 `draft_owner_id` 过滤）。已发布表不做任何修改。

## 5. 服务与 API 分层

### 5.1 服务层

- **Draft 写入**：  
  - 方案 A：在现有 `SceneMgmtService` / `ArchitectureService` 等中增加「写草稿」方法（如 `create_scene_draft`、`update_scene_draft`），现有「写主表」接口保留或改为仅内部/管理员使用。  
  - 方案 B：独立 `DraftService`，接收与现有 API 相同的 DTO，内部写草稿表并保证版本一致；列表/详情由「是否带 use_draft」决定查主表还是草稿表。
- **审批**：独立 `ApproveService.approve_version_draft(version_id)`，内部按上述顺序同步草稿 → 主表并清空草稿。
- **还原**：独立 `RevertService.revert_version_draft(version_id)`，仅删草稿表该版本数据。

### 5.2 API 设计建议

| 能力 | 方法 | 路径（示例） | 说明 |
|------|------|----------------|------|
| 保存草稿 | POST/PUT | 沿用现有场景/架构的 create/update，通过 query 如 `?use_draft=1` 或统一策略「写即草稿」 | 写草稿表 |
| 列表/详情 | GET | 沿用现有接口，增加 `?scope=published\|draft` 或 `use_draft=true` | 查主表或草稿表 |
| 审批入库 | POST | `/api/v1/versions/{version_id}/draft/approve` | 草稿 → 主表，清空草稿 |
| 还原修改 | POST | `/api/v1/versions/{version_id}/draft/revert` | 仅删草稿 |

列表与详情若需「未选则默认已发布」，可约定：`scope=published` 或未传时查主表；`scope=draft` 时查草稿表；前端可再提供「对比视图」用两次请求分别取 published 与 draft 做 diff。

## 6. 与现有代码的衔接

- **模型**：在 `app/domains/scene_mgmt/models/`、`app/domains/arch_mgmt/models/` 下新增 `*_draft` 表模型，结构复制自主表，便于复用 DTO 与校验。
- **场景/架构现有 API**：  
  - 若采用「写即草稿」，可将现有 create/update 实现改为写草稿表；或保留两套（写主表 / 写草稿），由配置或权限控制。  
  - 查询接口增加 `scope` 参数，在 Service 内根据 scope 选择查主表或草稿表并返回统一 DTO。
- **审批/还原**：可放在 `app/domains/product_mgmt`（版本维度）或新建 `app/domains/draft_mgmt`，调用各 domain 的草稿表与主表完成同步/清理。

## 7. 小结

- **双区存储**（已发布表 + 草稿表）、以**版本**为粒度，能清晰区分「已审批」与「待审批」，并支持一键还原。
- **审批** = 按依赖顺序把草稿合并进主表并清空草稿；**还原** = 只删草稿。
- 服务层可保留现有 Scene/Arch 服务，仅增加草稿读写与 `ApproveService`/`RevertService`；API 通过 `scope` 与两条新接口（approve/revert）暴露能力，便于前端实现「编辑 → 保存草稿 → 审批入库 / 还原」的完整流程。
