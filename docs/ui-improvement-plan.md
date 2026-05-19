# PioneClaw UI 全面改进方案

## 一、全局设计系统层

### 1.1 需要补充的全局工具类

Add these utility classes to main.scss:

```scss
// 渐变标题（所有页面统一使用）
.pc-page-title {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.3px;
  background: var(--pc-gradient-primary);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

// 统计卡片（Dashboard / Tasks / Skills 等页面复用）
.pc-stat-card {
  background: var(--pc-gradient-card);
  border: 1px solid var(--pc-border);
  border-radius: var(--pc-radius-lg);
  padding: 20px;
  transition: all 0.3s ease;
  
  &:hover {
    border-color: var(--pc-border-hover);
    box-shadow: var(--pc-shadow-glow);
  }
}

// 表格统一样式
.pc-data-table {
  .el-table__header th {
    background: rgba(var(--pc-primary-rgb), 0.04) !important;
    color: var(--pc-text-secondary);
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }
  
  .el-table__row {
    transition: all 0.2s ease;
    
    &:hover > td {
      background: rgba(var(--pc-primary-rgb), 0.03) !important;
    }
  }
}

// 空状态统一
.pc-empty-state {
  padding: 60px 20px;
  text-align: center;
  
  .el-empty__description {
    color: var(--pc-text-muted);
    font-size: 14px;
  }
}

// 操作栏统一
.pc-action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  .left { display: flex; gap: 12px; align-items: center; }
  .right { display: flex; gap: 8px; }
}
```

## 二、布局层（MainLayout.vue）

### 2.1 侧边栏活跃项指示器修复

Current issue: `::before` pseudo-element positioning
Fix: Change `left: 0` to `left: -8px` or adjust `position: relative` on `.nav-item`

### 2.2 侧边栏折叠后的 Tooltip

Add `el-tooltip` wrapper around icons when sidebar is collapsed:

```vue
<router-link to="/dashboard" class="nav-item" :class="{ active: activeMenu === '/dashboard' }">
  <el-tooltip :content="$t('nav.dashboard')" placement="right" :disabled="!isCollapsed">
    <el-icon><Odometer /></el-icon>
  </el-tooltip>
  <span class="nav-label" v-show="!isCollapsed">{{ $t('nav.dashboard') }}</span>
</router-link>
```

### 2.3 顶栏改进
- Add breadcrumb navigation in `header-left`
- Add keyboard shortcut hints in user dropdown

## 三、页面级改进

### 3.1 Dashboard.vue

Issues:
- Missing `v-loading`
- Stat cards missing gradient top line
- Data charts lack visual hierarchy

Add to each `.overview-card`:
```scss
.overview-card {
  position: relative;
  overflow: hidden;
  
  .card-accent-line {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: var(--pc-gradient-primary);
    opacity: 0.6;
  }
  
  &.gateway .card-accent-line { background: linear-gradient(90deg, var(--pc-accent-green), #34d399); }
  &.agents .card-accent-line { background: linear-gradient(90deg, var(--pc-primary), #60a5fa); }
  &.tasks .card-accent-line { background: linear-gradient(90deg, var(--pc-accent-orange), #fbbf24); }
  &.api .card-accent-line { background: linear-gradient(90deg, var(--pc-accent-purple), #a78bfa); }
}
```

### 3.2 Chat.vue

Issues:
- Empty state uses emoji (unprofessional)
- Message bubbles need contrast check in dark mode
- Missing message status indicators

Replace empty state emoji with SVG icon.
Add quick action buttons below empty state.
Add message status indicators (sending/sent/failed).

### 3.3 Agents.vue / Tasks.vue / Skills.vue (统一列表页)

Issues:
- Inconsistent structure across similar pages
- Missing visual separation between stat cards and tables
- Action button styles vary

Unify with:
- `pc-page-header` with gradient title
- `pc-stat-grid` with trend indicators
- `pc-filter-bar` with search + filters
- `pc-data-table` with consistent styling
- Pagination at bottom

### 3.4 Settings.vue

Issues:
- Uneven card heights with stretch
- Default Element Plus icons
- Inconsistent save button placement

Improvements:
- Better menu items with colored icons and descriptions
- Consistent card-based layout
- Section header with inline save button

### 3.5 Login.vue

Issues:
- Cyberpunk background may be too flashy
- Form area could be more premium
- Missing brand feature showcase

Add:
- Subtle gradient + grid background
- Left brand section with logo, tagline, features
- Right form section in elevated card
- Feature list with icons

## 四、组件级改进

### 4.1 表格操作列统一

Use icon buttons with tooltips, separated by vertical dividers:
- Edit: primary link + Edit icon
- Toggle: warning/success link + CircleClose/CircleCheck icon  
- Delete: danger link + Delete icon

### 4.2 状态标签统一

Use `el-tag` with `effect="light" size="small" round` plus colored dot indicator:
- Success: green dot + glow
- Warning: orange dot
- Danger: red dot
- Info: gray dot

## 五、交互体验改进

### 5.1 页面过渡动画

```scss
.page-enter-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.page-enter-from {
  opacity: 0;
  transform: translateY(10px);
}
```

### 5.2 Toast 通知样式

Customize ElMessage with border, shadow, and themed backgrounds.

### 5.3 键盘快捷键
- Cmd/Ctrl + K: Search
- Cmd/Ctrl + N: Create new
- Escape: Close dialogs

## 六、实施优先级

### 进度状态
- [x] **P0 已完成** (2026-05-07)
- [x] **P1 已完成** (2026-05-07)
- [x] **P2 已完成** (2026-05-07)
- [x] **P3 已完成** (2026-05-07)

| 优先级 | 改进项 | 影响范围 | 预估工作量 | 状态 |
|--------|--------|----------|-----------|------|
| P0 | 统一页面标题为渐变样式 | 所有页面 | 30min | ✅ 已完成 |
| P0 | 补充缺失的 v-loading | Dashboard, Wiki | 15min | ✅ 已完成 |
| P0 | 补充缺失的空状态 | Skills, Users, Dashboard | 30min | ✅ 已完成 |
| P1 | 统一表格样式（pc-data-table） | 所有列表页 | 1h | ✅ 已完成 |
| P1 | 统一操作列按钮样式 | 所有列表页 | 1h | ✅ 已完成 |
| P1 | 统计卡片统一改进 | Dashboard, Tasks, Skills | 1h | ✅ 已完成 |
| P2 | Chat 页面空状态 + 快捷操作 | Chat.vue | 1h | ✅ 已完成 |
| P2 | Settings 页面菜单改进 | Settings.vue | 1h | ✅ 已完成 |
| P2 | Login 页面品牌区 | Login.vue | 1.5h | ✅ 已完成 |
| P3 | 添加页面过渡动画 | 全局 | 30min | ✅ 已存在 |
| P3 | 添加键盘快捷键 | 全局 | 30min | ✅ 已完成 |
| P2 | Chat 页面空状态 + 快捷操作 | Chat.vue | 1h |
| P2 | Settings 页面菜单改进 | Settings.vue | 1h |
| P2 | Login 页面品牌区 | Login.vue | 1.5h |
| P3 | 添加页面过渡动画 | 全局 | 30min |
| P3 | 添加键盘快捷键 | 全局 | 30min |

## 七、验收检查清单

- [ ] 暗色模式下所有文字清晰可读
- [ ] Hover 状态在所有可交互元素上一致
- [ ] 间距使用 4/8/16/24/32px 阶梯
- [ ] 阴影层次正确（card sm / dropdown lg / modal lg）
- [ ] 圆角统一（6px / 10px / 14px）
- [ ] 所有页面有渐变标题
- [ ] 所有列表页有空状态
- [ ] 所有页面有加载状态

---

Created: 2026-05-06
