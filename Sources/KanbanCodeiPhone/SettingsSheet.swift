import SwiftUI

struct SettingsSheet: View {
    @Environment(\.dismiss) private var dismiss
    @AppStorage("appearanceMode") private var appearanceMode = "auto"
    @AppStorage("notificationsEnabled") private var notificationsEnabled = true
    @AppStorage("serverHost") private var serverHost = ""

    var body: some View {
        NavigationStack {
            Form {
                Section("Appearance") {
                    Picker("Theme", selection: $appearanceMode) {
                        Text("Auto").tag("auto")
                        Text("Light").tag("light")
                        Text("Dark").tag("dark")
                    }
                }

                Section("Notifications") {
                    Toggle("Push Notifications", isOn: $notificationsEnabled)
                }

                Section("Connection") {
                    TextField("Server Host (optional)", text: $serverHost)
                        #if os(iOS)
                        .textInputAutocapitalization(.never)
                        .keyboardType(.URL)
                        #endif
                        .autocorrectionDisabled()

                    Text("Connect to a Mac running Kanban Code to sync sessions in real-time.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Section("About") {
                    LabeledContent("Version", value: "1.0.0 (iPhone)")
                    Link("GitHub Repository", destination: URL(string: "https://github.com/langwatch/kanban-code")!)
                    Link("Report an Issue", destination: URL(string: "https://github.com/langwatch/kanban-code/issues")!)
                }
            }
            .navigationTitle("Settings")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}
