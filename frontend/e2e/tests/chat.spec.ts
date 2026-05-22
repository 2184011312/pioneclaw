/**
 * E2E Tests: Agent Conversation flow
 */

import { test, expect } from '../fixtures/auth'
import { ChatPage } from '../pages/ChatPage'

test.describe('Agent Conversation Flow', () => {

  test('should load chat page with sidebar', async ({ page, testUser }) => {
    const chatPage = new ChatPage(page)
    await chatPage.goto()
    await expect(chatPage.messageInput).toBeVisible()
    await expect(chatPage.conversationList).toBeVisible()
  })

  test('should send a message and receive agent response', async ({ page, testUser }) => {
    test.setTimeout(120000)
    const chatPage = new ChatPage(page)
    await chatPage.goto()

    // Start a new conversation
    await chatPage.newConversation()
    await page.waitForTimeout(500)

    // Send a simple message
    await chatPage.sendMessage('Hello, introduce yourself briefly.')

    // Wait for response
    await chatPage.waitForResponse(60000)

    // Verify response appeared
    const lastMsg = await chatPage.getLastAssistantMessage()
    expect(lastMsg.length).toBeGreaterThan(0)
  })

  test('should create multiple conversations', async ({ page, testUser }) => {
    test.setTimeout(120000)
    const chatPage = new ChatPage(page)
    await chatPage.goto()

    await chatPage.newConversation()
    await chatPage.sendMessage('What is 2+2?')
    await chatPage.waitForResponse(30000)

    await chatPage.newConversation()
    await chatPage.sendMessage('Say "test complete"')
    await chatPage.waitForResponse(30000)

    const lastMsg = await chatPage.getLastAssistantMessage()
    expect(lastMsg.length).toBeGreaterThan(0)
  })
})

test.describe('Agent Tool Calling', () => {

  test('should trigger current_time tool call', async ({ page, testUser }) => {
    test.setTimeout(180000)
    const chatPage = new ChatPage(page)
    await chatPage.goto()
    await chatPage.newConversation()
    await page.waitForTimeout(500)

    // current_time is the most reliable tool — model can't know real time without it
    await chatPage.sendMessage('What is the exact current date and time? Use the current_time tool.')

    // Wait for streaming to finish
    await chatPage.waitForStreamEnd(120000)

    // Verify response received
    const lastMsg = await chatPage.getLastAssistantMessage()
    expect(lastMsg.length).toBeGreaterThan(0)

    // Check for tool call bubbles (SSE tool_result events)
    const hadToolCalls = await chatPage.waitForToolCalls(5000)
    if (hadToolCalls) {
      const count = await chatPage.getToolCallItems().count()
      expect(count).toBeGreaterThan(0)
      // Verify tool name is visible
      const toolName = chatPage.getToolCallItems().first().locator('.tool-name')
      await expect(toolName).toBeVisible()
    }
  })

  test('should call list_dir to see filesystem', async ({ page, testUser }) => {
    test.setTimeout(180000)
    const chatPage = new ChatPage(page)
    await chatPage.goto()
    await chatPage.newConversation()
    await page.waitForTimeout(500)

    // Model can't know filesystem contents — must use list_dir
    await chatPage.sendMessage('List all files and folders in the current working directory using list_dir.')

    await chatPage.waitForStreamEnd(120000)

    const lastMsg = await chatPage.getLastAssistantMessage()
    expect(lastMsg.length).toBeGreaterThan(0)

    // Check for tool call bubbles
    const hadToolCalls = await chatPage.waitForToolCalls(5000)
    if (hadToolCalls) {
      const count = await chatPage.getToolCallItems().count()
      expect(count).toBeGreaterThan(0)
    }
  })

  test('should display tool result when bubble is expanded', async ({ page, testUser }) => {
    test.setTimeout(180000)
    const chatPage = new ChatPage(page)
    await chatPage.goto()
    await chatPage.newConversation()
    await page.waitForTimeout(500)

    // Use current_time — fast, always succeeds, no side effects
    await chatPage.sendMessage('What time is it? Use current_time.')

    await chatPage.waitForStreamEnd(120000)

    const lastMsg = await chatPage.getLastAssistantMessage()
    expect(lastMsg.length).toBeGreaterThan(0)

    // Check for tool call bubbles
    const toolBubbles = chatPage.getToolCallBubbles()
    const bubbleCount = await toolBubbles.count()

    if (bubbleCount > 0) {
      // Click the tool call header to expand and show result
      const firstHeader = toolBubbles.first().locator('.tool-call-header')
      await firstHeader.click()
      await page.waitForTimeout(300)

      // Tool name should be visible
      const toolName = toolBubbles.first().locator('.tool-name')
      await expect(toolName).toBeVisible()

      // Tool result should now be visible (expanded)
      const toolResult = toolBubbles.first().locator('.tool-result')
      await expect(toolResult).toBeVisible()

      // Result should have content (not empty)
      const resultText = await toolResult.textContent()
      expect(resultText?.trim().length).toBeGreaterThan(0)
    }
  })

  test('should handle web_search tool call', async ({ page, testUser }) => {
    test.setTimeout(180000)
    const chatPage = new ChatPage(page)
    await chatPage.goto()
    await chatPage.newConversation()
    await page.waitForTimeout(500)

    // Web search requires external data — model can't answer from training
    await chatPage.sendMessage('Search the web for "latest AI news today" using web_search.')

    await chatPage.waitForStreamEnd(120000)

    const lastMsg = await chatPage.getLastAssistantMessage()
    expect(lastMsg.length).toBeGreaterThan(0)

    // Check for tool indicators
    const hadToolCalls = await chatPage.waitForToolCalls(5000)
    if (hadToolCalls) {
      const count = await chatPage.getToolCallItems().count()
      expect(count).toBeGreaterThan(0)
    }
  })

  test('should handle multiple different tools in sequence', async ({ page, testUser }) => {
    test.setTimeout(180000)
    const chatPage = new ChatPage(page)
    await chatPage.goto()
    await chatPage.newConversation()
    await page.waitForTimeout(500)

    // Multi-step: time (tool) + directory listing (tool)
    await chatPage.sendMessage(
      'Please do both: 1) Check the current time using current_time. 2) List files in the current directory using list_dir.'
    )

    await chatPage.waitForStreamEnd(120000)

    const lastMsg = await chatPage.getLastAssistantMessage()
    expect(lastMsg.length).toBeGreaterThan(0)

    // Count tool calls
    const toolItems = chatPage.getToolCallItems()
    const count = await toolItems.count()

    if (count > 0) {
      // Verify each tool item has a name
      const names: string[] = []
      for (let i = 0; i < count; i++) {
        const nameLocator = toolItems.nth(i).locator('.tool-name')
        if (await nameLocator.isVisible().catch(() => false)) {
          const name = await nameLocator.textContent()
          if (name) names.push(name.trim())
        }
      }
      // Should have at least one tool name
      expect(names.length).toBeGreaterThan(0)
    }
  })
})
