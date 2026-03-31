import Foundation

/// Sends push notifications via the Pushover API.
public final class PushoverClient: NotifierPort, @unchecked Sendable {
    private let token: String
    private let userKey: String
    private let apiURL = URL(string: "https://api.pushover.net/1/messages.json")!

    public init(token: String, userKey: String) {
        self.token = token
        self.userKey = userKey
    }

    public func sendNotification(title: String, message: String, imageData: Data?, cardId: String?) async throws {
        var request = URLRequest(url: apiURL)
        request.httpMethod = "POST"

        let boundary = "Boundary-\(UUID().uuidString)"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")

        var body = Data()

        func addField(_ name: String, _ value: String) {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"\(name)\"\r\n\r\n".data(using: .utf8)!)
            body.append("\(value)\r\n".data(using: .utf8)!)
        }

        addField("token", token)
        addField("user", userKey)
        addField("title", title)
        addField("message", message)
        addField("html", "1")

        if let cardId {
            addField("url", "kanbancode://card/\(cardId)")
            addField("url_title", "Open in Kanban Code")
        }

        if let imageData {
            body.append("--\(boundary)\r\n".data(using: .utf8)!)
            body.append("Content-Disposition: form-data; name=\"attachment\"; filename=\"image.png\"\r\n".data(using: .utf8)!)
            body.append("Content-Type: image/png\r\n\r\n".data(using: .utf8)!)
            body.append(imageData)
            body.append("\r\n".data(using: .utf8)!)
        }

        body.append("--\(boundary)--\r\n".data(using: .utf8)!)
        request.httpBody = body

        let (_, response) = try await URLSession.shared.data(for: request)
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw NotificationError.pushoverFailed
        }
    }

    public func isConfigured() -> Bool {
        !token.isEmpty && !userKey.isEmpty
    }
}

public enum NotificationError: Error, LocalizedError {
    case pushoverFailed
    case macOSNotificationFailed

    public var errorDescription: String? {
        switch self {
        case .pushoverFailed: "Pushover notification failed"
        case .macOSNotificationFailed: "macOS notification failed"
        }
    }
}
