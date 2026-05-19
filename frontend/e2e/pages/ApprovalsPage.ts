/**
 * Approvals Page Object — Approval workflow
 */

import { Page, Locator } from '@playwright/test'
import { BasePage } from './BasePage'

export class ApprovalsPage extends BasePage {
  readonly pendingTab: Locator
  readonly approvedTab: Locator
  readonly approvalList: Locator
  readonly createButton: Locator

  constructor(page: Page) {
    super(page)
    this.pendingTab = page.getByRole('tab', { name: /待审批|Pending/i })
    this.approvedTab = page.getByRole('tab', { name: /已审批|Approved/i })
    this.approvalList = page.locator('.el-table, .approval-list').first()
    this.createButton = page.getByRole('button', { name: /提交审批|New Approval|Create/i }).first()
  }

  async goto() {
    await this.navigate('/extension-management')
  }

  /** Submit a new approval request */
  async submitApproval(type: string, detail: string) {
    await this.createButton.click()
    await this.page.waitForSelector('.el-dialog:visible, .el-drawer:visible', { timeout: 5000 })

    // Select approval type
    const typeSelect = this.page.locator('.el-select').first()
    await typeSelect.click()
    await this.page.locator('.el-select-dropdown__item', { hasText: type }).click()

    // Fill detail
    await this.page.locator('textarea').first().fill(detail)

    // Submit
    await this.page.getByRole('button', { name: /提交|Submit/i }).click()
  }

  /** Approve a pending request */
  async approveRequest(containsText: string) {
    const row = this.approvalList.locator('tr', { hasText: containsText }).first()
    await row.getByRole('button', { name: /通过|Approve/i }).click()
  }

  /** Reject a pending request */
  async rejectRequest(containsText: string) {
    const row = this.approvalList.locator('tr', { hasText: containsText }).first()
    await row.getByRole('button', { name: /拒绝|Reject/i }).click()
  }

  /** Expect a request with given text and status */
  async expectRequestStatus(containsText: string, status: string) {
    const row = this.approvalList.locator('tr', { hasText: containsText }).first()
    await expect(row).toBeVisible()
    await expect(row.locator('td', { hasText: status }).first()).toBeVisible()
  }
}
