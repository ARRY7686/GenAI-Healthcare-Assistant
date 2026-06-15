import { test, expect } from '@playwright/test'

const SHOTS = 'e2e/__screenshots__'

// Fill the consent gate. Returns the (initially disabled) "Accept & start" button.
async function fillConsent(page, { age, sex, pregnant = false }) {
  await page.goto('/triage')
  await expect(page.getByText('Before we begin')).toBeVisible()
  const accept = page.getByRole('button', { name: /start symptom check/i })
  await expect(accept).toBeDisabled() // gate blocks until consent + demographics
  await page.getByRole('button', { name: age }).click()
  await page.getByRole('button', { name: sex, exact: true }).click()
  if (pregnant) await page.getByLabel(/I am currently pregnant/i).check()
  await page.getByLabel(/I understand this is triage guidance/i).check()
  await expect(accept).toBeEnabled()
  return accept
}

async function answer(page, text) {
  await page.getByPlaceholder(/Describe your symptoms/i).fill(text)
  await page.getByRole('button', { name: 'Send' }).click()
}

test('consent → adaptive questioning → completion (features #1–2)', async ({ page }) => {
  const accept = await fillConsent(page, { age: /16.?39/, sex: 'Male' })
  await page.screenshot({ path: `${SHOTS}/01-consent.png`, fullPage: true })
  await accept.click()

  // Feature #1 — opening question
  await expect(page.getByText('What is your main symptom or concern today?')).toBeVisible()

  // Feature #2 — turn 1 → adaptive question WITH its rationale
  await answer(page, 'I have a headache')
  await expect(page.getByText(/mild, moderate, or severe/i)).toBeVisible()
  await expect(page.getByText(/Why I.?m asking/i)).toBeVisible()
  await page.screenshot({ path: `${SHOTS}/02-adaptive-question.png`, fullPage: true })

  // turn 2 → a DIFFERENT, more specific question (adaptive narrowing)
  await answer(page, 'it is moderate and came on gradually')
  await expect(page.getByText(/How long has this been going on/i)).toBeVisible()

  // turn 3 → enough info collected → completion
  await answer(page, 'about two days, and some nausea too')
  await expect(page.getByText('Symptom check complete')).toBeVisible()
  await expect(page.getByRole('link', { name: /View assessment/i })).toBeVisible()
  await page.screenshot({ path: `${SHOTS}/03-complete.png`, fullPage: true })
})

test('consent gate refuses under-16 up front (scope)', async ({ page }) => {
  const accept = await fillConsent(page, { age: 'Under 16', sex: 'Male' })
  await accept.click()
  await expect(page.getByText(/continue here/i)).toBeVisible()
  await expect(page.getByText(/adults 16 and older/i)).toBeVisible()
  await page.screenshot({ path: `${SHOTS}/04-refusal-minor.png`, fullPage: true })
})

test('consent gate refuses pregnancy up front (scope)', async ({ page }) => {
  const accept = await fillConsent(page, { age: /16.?39/, sex: 'Female', pregnant: true })
  await accept.click()
  await expect(page.getByText(/during pregnancy/i)).toBeVisible()
})

test('assessment & summary shells render (features #3–6)', async ({ page }) => {
  await page.goto('/summary')
  await expect(page.getByText('Assessment & Summary')).toBeVisible()
  await expect(page.getByText(/Preview/i)).toBeVisible()
  // Emergency scenario surfaces the feature #6 safety banner.
  await page.getByRole('button', { name: 'Emergency' }).click()
  await expect(page.getByText(/This may be a medical emergency/i)).toBeVisible()
  await page.screenshot({ path: `${SHOTS}/05-summary.png`, fullPage: true })
})
