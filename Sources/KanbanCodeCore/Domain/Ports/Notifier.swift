import Foundation

/// Port for sending notifications to the user.
public protocol NotifierPort: Sendable {
    /// Send a notification with optional image attachment and card ID for click handling.
    func sendNotification(title: String, message: String, imageData: Data?, cardId: String?) async throws

    /// Check if this notifier is configured and ready.
    func isConfigured() -> Bool
}
