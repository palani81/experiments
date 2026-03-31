import Foundation

/// Anti-duplicate logic for notifications.
/// Mirrors claude-pushover's exact approach, adapted for batch processing:
/// - Stop: sleep 1s, check if user prompted within 1s after stop → if not, send (with 62s dedup)
/// - Notification: send if not within 62s dedup window
/// - UserPromptSubmit: record timestamp for debounce check
///
/// Key difference from claude-pushover: we process events in batches (not one-per-process),
/// so we use EVENT TIMESTAMPS (from the hook script) instead of wall-clock Date() to avoid
/// batch processing artifacts where future events in the batch pollute earlier events.
public actor NotificationDeduplicator {
    /// Per-session last notification event time (for 62s dedup window).
    private var lastNotified: [String: Date] = [:]
    /// Per-session last prompt event time (for Stop debounce).
    private var lastPromptTime: [String: Date] = [:]
    /// Dedup window in seconds.
    private let dedupWindow: TimeInterval

    public init(dedupWindow: TimeInterval = 62) {
        self.dedupWindow = dedupWindow
    }

    /// Record a UserPromptSubmit using the event's actual timestamp.
    public func recordPrompt(sessionId: String, at eventTime: Date) {
        lastPromptTime[sessionId] = eventTime
    }

    /// Check if user prompted within 1s after a Stop event.
    /// Uses event timestamps to correctly handle batch processing:
    /// only blocks if the prompt came within 1s AFTER the stop (matching claude-pushover's 1s sleep window).
    public func hasPromptedWithin(sessionId: String, after stopTime: Date, window: TimeInterval = 1.0) -> Bool {
        guard let promptTime = lastPromptTime[sessionId] else { return false }
        return promptTime > stopTime && promptTime <= stopTime.addingTimeInterval(window)
    }

    /// Check 62s dedup window using event timestamps.
    /// Returns true if notification should be sent.
    public func shouldNotify(sessionId: String, eventTime: Date) -> Bool {
        if let lastTime = lastNotified[sessionId] {
            if eventTime.timeIntervalSince(lastTime) < dedupWindow { return false }
        }
        lastNotified[sessionId] = eventTime
        return true
    }

    /// Clear all state (used on startup to discard stale events).
    public func clearAllPending() {
        lastPromptTime.removeAll()
    }
}
