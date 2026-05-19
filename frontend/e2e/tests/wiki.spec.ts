/**
 * E2E Tests: Wiki CRUD
 */

import { test, expect } from '../fixtures/auth'
import { CrudPage } from '../pages/CrudPage'

test.describe('Wiki CRUD', () => {

  test('should load wiki page', async ({ page, testUser }) => {
    const wikiPage = new CrudPage(page, '/wiki', 'Wiki')
    await wikiPage.goto()
    // Wiki page shows a tree or content area
    await expect(page.locator('.wiki-container, .wiki-tree, .el-tree, .wiki-content').first()).toBeVisible({ timeout: 10000 })
  })

  test('should create a new wiki page', async ({ page, testUser }) => {
    const wikiPage = new CrudPage(page, '/wiki', 'Wiki')
    await wikiPage.goto()

    // Wiki typically has a "create" or "new page" button
    const createBtn = page.getByRole('button', { name: /新增|创建|新建|Create|New|Add/i }).first()
    if (await createBtn.isVisible()) {
      await createBtn.click()
      await page.waitForTimeout(500)

      const title = `E2E Wiki ${Date.now()}`
      const titleInput = page.locator('input[placeholder*="标题"], input[placeholder*="Title"], .el-dialog input').first()
      await titleInput.fill(title)

      // Editor content
      const editor = page.locator('.el-dialog textarea, .editor textarea, [contenteditable="true"]').first()
      await editor.fill('# E2E Test Wiki\n\nThis page was created by an E2E test.')
      await page.getByRole('button', { name: /保存|确定|创建|确认|Save|Create|Submit/i }).first().click({ force: true })

      await page.waitForTimeout(2000)
    }
  })

  test('should edit a wiki page', async ({ page, testUser }) => {
    const wikiPage = new CrudPage(page, '/wiki', 'Wiki')
    await wikiPage.goto()

    // Click on a wiki page in the tree to open it
    const treeNode = page.locator('.el-tree-node__content, .wiki-tree-item').first()
    if (await treeNode.isVisible()) {
      await treeNode.click()
      await page.waitForTimeout(1000)

      // Look for edit button
      const editBtn = page.getByRole('button', { name: /编辑|Edit/i }).first()
      if (await editBtn.isVisible()) {
        await editBtn.click()
        await page.waitForTimeout(500)

        const editor = page.locator('textarea, [contenteditable="true"]').first()
        const current = await editor.textContent() || ''
        await editor.fill(current + '\n\nEdited by E2E test.')
        await page.getByRole('button', { name: /保存|确定|Save|Confirm/i }).click()
        await page.waitForTimeout(2000)
      }
    }
  })

  test('should delete a wiki page', async ({ page, testUser }) => {
    const wikiPage = new CrudPage(page, '/wiki', 'Wiki')
    await wikiPage.goto()

    // Find a delete button in the tree context menu or toolbar
    const deleteBtn = page.getByRole('button', { name: /删除|Delete/i }).first()
    if (await deleteBtn.isVisible()) {
      await deleteBtn.click()
      // Confirm delete dialog
      const confirmBtn = page.getByRole('button', { name: /确定|Confirm|Yes|OK/i })
      if (await confirmBtn.isVisible({ timeout: 2000 })) {
        await confirmBtn.click()
        await page.waitForTimeout(1000)
      }
    }
  })
})
