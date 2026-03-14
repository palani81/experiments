import Foundation

/// Tries a primary notifier (e.g. Pushover), falls back to a secondary (e.g. macOS).
public final class CompositeNotifier: NotifierPort, @unchecked Sendable {
    private var primary: NotifierPort?
    private let fallback: NotifierPort

    public init(primary: NotifierPort? = nil, fallback: NotifierPort = MacOSNotificationClient()) {
        self.primary = primary
        self.fallback = fallback
    }

    public func sendNotification(title: String, message: String, imageData: Data?, cardId: String?) async throws {
        if let primary, primary.isConfigured() {
            do {
                try await primary.sendNotification(title: title, message: message, imageData: imageData, cardId: cardId)
                return
            } catch {
                // Fall through to fallback
            }
        }
        // Fallback doesn't support images, send text only
        try await fallback.sendNotification(title: title, message: message, imageData: nil, cardId: cardId)
    }

    public func isConfigured() -> Bool {
        true // Always configured — fallback is always available
    }

    /// Hot-swap the primary notifier (e.g. when settings change).
    public func updatePrimary(_ notifier: NotifierPort?) {
        self.primary = notifier
    }
}
