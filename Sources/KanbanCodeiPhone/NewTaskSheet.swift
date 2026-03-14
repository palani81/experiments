import SwiftUI

struct NewTaskSheet: View {
    var onAdd: (String, String?) -> Void
    @Environment(\.dismiss) private var dismiss
    @State private var taskName = ""
    @State private var projectPath = ""
    @FocusState private var isNameFocused: Bool

    var body: some View {
        NavigationStack {
            Form {
                Section("Task") {
                    TextField("Task name", text: $taskName)
                        .focused($isNameFocused)
                }

                Section("Project (optional)") {
                    TextField("Project path", text: $projectPath)
                        #if os(iOS)
                        .textInputAutocapitalization(.never)
                        #endif
                        .autocorrectionDisabled()
                }
            }
            .navigationTitle("New Task")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Add") {
                        let project = projectPath.isEmpty ? nil : projectPath
                        onAdd(taskName, project)
                        dismiss()
                    }
                    .disabled(taskName.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
            .onAppear {
                isNameFocused = true
            }
        }
    }
}
