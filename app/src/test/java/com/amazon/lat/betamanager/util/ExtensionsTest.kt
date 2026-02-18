package com.amazon.lat.betamanager.util

import org.junit.Assert.*
import org.junit.Test

/**
 * Unit tests for extension functions in [Extensions.kt].
 */
class ExtensionsTest {

    // ── toRelativeTimeString() ──

    @Test
    fun `toRelativeTimeString just now for recent timestamps`() {
        val recent = System.currentTimeMillis() - 30_000L // 30 seconds ago
        assertEquals("just now", recent.toRelativeTimeString())
    }

    @Test
    fun `toRelativeTimeString minutes ago`() {
        val fiveMinAgo = System.currentTimeMillis() - 300_000L // 5 minutes ago
        val result = fiveMinAgo.toRelativeTimeString()
        assertTrue("Should show minutes: $result", result.endsWith("m ago"))
        assertTrue("Should be around 5m: $result", result.startsWith("5") || result.startsWith("4"))
    }

    @Test
    fun `toRelativeTimeString hours ago`() {
        val threeHoursAgo = System.currentTimeMillis() - 10_800_000L // 3 hours ago
        val result = threeHoursAgo.toRelativeTimeString()
        assertTrue("Should show hours: $result", result.endsWith("h ago"))
    }

    @Test
    fun `toRelativeTimeString days ago`() {
        val twoDaysAgo = System.currentTimeMillis() - 172_800_000L // 2 days ago
        val result = twoDaysAgo.toRelativeTimeString()
        assertTrue("Should show days: $result", result.endsWith("d ago"))
    }

    @Test
    fun `toRelativeTimeString full date for older timestamps`() {
        val twoWeeksAgo = System.currentTimeMillis() - 1_209_600_000L // 2 weeks ago
        val result = twoWeeksAgo.toRelativeTimeString()
        // Should be a formatted date like "Jan 15, 2025"
        assertTrue("Should contain a comma for date format: $result", result.contains(","))
    }

    // ── toFormattedSize() ──

    @Test
    fun `toFormattedSize KB for small sizes`() {
        val size = 500_000L
        val result = size.toFormattedSize()
        assertTrue("Should show KB: $result", result.endsWith("KB"))
        assertEquals("500.0 KB", result)
    }

    @Test
    fun `toFormattedSize MB for medium sizes`() {
        val size = 45_000_000L
        val result = size.toFormattedSize()
        assertTrue("Should show MB: $result", result.endsWith("MB"))
        assertEquals("45.0 MB", result)
    }

    @Test
    fun `toFormattedSize GB for large sizes`() {
        val size = 2_500_000_000L
        val result = size.toFormattedSize()
        assertTrue("Should show GB: $result", result.endsWith("GB"))
        assertEquals("2.50 GB", result)
    }

    @Test
    fun `toFormattedSize zero bytes`() {
        val size = 0L
        val result = size.toFormattedSize()
        assertEquals("0.0 KB", result)
    }

    @Test
    fun `toFormattedSize boundary between KB and MB`() {
        val justUnderMB = 999_999L
        val atMB = 1_000_000L

        assertTrue("999,999 should be KB", justUnderMB.toFormattedSize().endsWith("KB"))
        assertTrue("1,000,000 should be MB", atMB.toFormattedSize().endsWith("MB"))
    }

    @Test
    fun `toFormattedSize boundary between MB and GB`() {
        val justUnderGB = 999_999_999L
        val atGB = 1_000_000_000L

        assertTrue("999,999,999 should be MB", justUnderGB.toFormattedSize().endsWith("MB"))
        assertTrue("1,000,000,000 should be GB", atGB.toFormattedSize().endsWith("GB"))
    }
}
