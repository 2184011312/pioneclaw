/**
 * Runners Page Object — Runner management & Center communication
 * Note: Runners.vue exists but has NO dedicated route.
 * It's embedded in AI Management or accessed via internal tab navigation.
 */

import { Page, Locator } from '@playwright/test'
import { BasePage } from './BasePage'

export class RunnersPage extends BasePage {
  readonly runnerCards: Locator
  readonly addButton: Locator
  readonly searchInput: Locator

  constructor(page: Page) {
    super(page)
    this.runnerCards = page.locator('.runner-card, .el-card, [class*="runner"]').first()
    this.addButton = page.getByRole('button', { name: /添加|新增|注册|Add|New|Register/i }).first()
    this.searchInput = page.locator('input[placeholder*="搜索"], input[placeholder*="Search"]').first()
  }

  /**
   * Navigate to runners section.
   * Runners are not directly routed — try common paths.
   */
  async goto() {
    // Try direct runner page first, then fall back to system-ops or ai-management
    const paths = ['/runners', '/system-ops', '/ai-management']
    for (const path of paths) {
      await this.navigate(path)
      // Check if we see runner-related content
      const hasRunnerContent = await this.page.locator('[class*="runner"], text=Runner, text=runner').first().isVisible().catch(() => false)
      if (hasRunnerContent) return
    }
    // Just stay on whatever page last loaded
    await this.navigate('/system-ops')
  }

  /** Approve a pending runner by name */
  async approveRunner(runnerName: string) {
    const card = this.page.locator('[class*="runner-card"], .el-card, tr', { hasText: runnerName }).first()
    await card.getByRole('button', { name: /通过|Approve|关联/i }).click()
    // Handle confirm dialog
    const confirmBtn = this.page.getByRole('button', { name: /确定|确认|OK|Yes/i })
    if (await confirmBtn.isVisible({ timeout: 2000 }).catch(() => false)) {
      await confirmBtn.click()
    }
  }

  /** Reject a pending runner */
  async rejectRunner(runnerName: string, reason?: string) {
    const card = this.page.locator('[class*="runner-card"], .el-card, tr', { hasText: runnerName }).first()
    await card.getByRole('button', { name: /拒绝|Reject/i }).click()
    if (reason) {
      const textarea = this.page.locator('textarea')
      if (await textarea.isVisible({ timeout: 2000 }).catch(() => false)) {
        await textarea.fill(reason)
        await this.page.getByRole('button', { name: /确定|Confirm/i }).click()
      }
    }
  }

  /** Verify runner is visible on the page */
  async expectRunnerVisible(name: string) {
    await expect(this.page.locator('[class*="runner-card"], .el-card, tr', { hasText: name }).first()).toBeVisible({ timeout: 5000 })
  }
}
