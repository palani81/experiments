import SwiftUI
import UserNotifications
import KanbanCodeCore

@main
struct KanbanCodeiPhoneApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}

final class AppDelegate: NSObject, UIApplicationDelegate, UNUserNotificationCenterDelegate {
    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        let center = UNUserNotificationCenter.current()
        center.delegate = self
        center.requestAuthorization(options: [.alert, .sound, .badge]) { granted, error in
            if let error {
                print("[Kanban Code] Notification permission error: \(error)")
            }
        }
        return true
    }

    // Show notifications even when the app is in the foreground
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        willPresent notification: UNNotification,
        withCompletionHandler completionHandler: @escaping (UNNotificationPresentationOptions) -> Void
    ) {
        completionHandler([.banner, .sound])
    }

    // Handle notification tap — select the card
    func userNotificationCenter(
        _ center: UNUserNotificationCenter,
        didReceive response: UNNotificationResponse,
        withCompletionHandler completionHandler: @escaping () -> Void
    ) {
        if let cardId = response.notification.request.content.userInfo["cardId"] as? String {
            NotificationCenter.default.post(
                name: .kanbanCodeSelectCard,
                object: nil,
                userInfo: ["cardId": cardId]
            )
        }
        completionHandler()
    }
}

// MARK: - Notification Names

extension Notification.Name {
    static let kanbanCodeNewTask = Notification.Name("kanbanCodeNewTask")
    static let kanbanCodeToggleSearch = Notification.Name("kanbanCodeToggleSearch")
    static let kanbanCodeHookEvent = Notification.Name("kanbanCodeHookEvent")
    static let kanbanCodeHistoryChanged = Notification.Name("kanbanCodeHistoryChanged")
    static let kanbanCodeSettingsChanged = Notification.Name("kanbanCodeSettingsChanged")
    static let kanbanCodeSelectCard = Notification.Name("kanbanCodeSelectCard")
}
