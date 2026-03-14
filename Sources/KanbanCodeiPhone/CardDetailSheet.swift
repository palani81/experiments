import SwiftUI
import KanbanCodeCore

/// Full-screen detail view for a card on iPhone.
struct CardDetailSheet: View {
    let card: KanbanCodeCard
    @Environment(\.dismiss) private var dismiss
    @State private var selectedTab: DetailTab = .info

    enum DetailTab: String, CaseIterable {
        case info = "Info"
        case history = "History"
        case actions = "Actions"
    }

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Tab picker
                Picker("", selection: $selectedTab) {
                    ForEach(DetailTab.allCases, id: \.self) { tab in
                        Text(tab.rawValue).tag(tab)
                    }
                }
                .pickerStyle(.segmented)
                .padding(.horizontal, 16)
                .padding(.vertical, 8)

                // Tab content
                switch selectedTab {
                case .info:
                    infoView
                case .history:
                    historyPlaceholder
                case .actions:
                    actionsView
                }
            }
            .navigationTitle(card.displayTitle)
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

    // MARK: - Info Tab

    private var infoView: some View {
        List {
            // Status section
            Section("Status") {
                LabeledContent("Column", value: card.column.displayName)
                LabeledContent("Label", value: card.link.cardLabel.rawValue)
                LabeledContent("Last Activity", value: card.relativeTime)

                if card.link.isRemote {
                    Label("Remote Execution", systemImage: "cloud")
                        .foregroundStyle(.teal)
                }
            }

            // Project & Branch
            Section("Project") {
                if let projectName = card.projectName {
                    LabeledContent("Project", value: projectName)
                }
                if let path = card.link.projectPath {
                    LabeledContent("Path") {
                        Text(path)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                            .lineLimit(2)
                    }
                }
                if let branch = card.link.worktreeLink?.branch {
                    LabeledContent("Branch", value: branch)
                }
            }

            // Session info
            if let session = card.link.sessionLink {
                Section("Session") {
                    LabeledContent("Session ID") {
                        Text(session.sessionId)
                            .font(.caption.monospaced())
                            .foregroundStyle(.secondary)
                    }
                    if let num = session.sessionNumber {
                        LabeledContent("Session #", value: "\(num)")
                    }

                    if card.isActivelyWorking {
                        Label("Actively Working", systemImage: "gear.circle.fill")
                            .foregroundStyle(.green)
                    }
                }
            }

            // Terminal
            if let tmux = card.link.tmuxLink {
                Section("Terminal") {
                    LabeledContent("Session", value: tmux.sessionName)
                    LabeledContent("Terminals", value: "\(tmux.terminalCount)")
                    if tmux.isShellOnly == true {
                        Label("Shell Only", systemImage: "terminal")
                            .foregroundStyle(.secondary)
                    }
                }
            }

            // Pull Requests
            if !card.link.prLinks.isEmpty {
                Section("Pull Requests") {
                    ForEach(card.link.prLinks, id: \.number) { pr in
                        Button {
                            if let urlString = pr.url, let url = URL(string: urlString) {
                                openURL(url)
                            }
                        } label: {
                            HStack {
                                VStack(alignment: .leading, spacing: 2) {
                                    Text(pr.title ?? "PR #\(pr.number)")
                                        .font(.body)
                                        .foregroundStyle(.primary)
                                    Text("#\(pr.number)")
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                }
                                Spacer()
                                if let status = pr.status {
                                    Text(status.rawValue)
                                        .font(.caption)
                                        .padding(.horizontal, 6)
                                        .padding(.vertical, 2)
                                        .background(prStatusColor(status).opacity(0.15), in: Capsule())
                                        .foregroundStyle(prStatusColor(status))
                                }
                                Image(systemName: "arrow.up.right.square")
                                    .font(.caption)
                                    .foregroundStyle(.secondary)
                            }
                        }
                    }
                }
            }

            // Issue
            if let issue = card.link.issueLink {
                Section("Issue") {
                    Button {
                        if let urlString = issue.url, let url = URL(string: urlString) {
                            openURL(url)
                        }
                    } label: {
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(issue.title ?? "Issue #\(issue.number)")
                                    .font(.body)
                                    .foregroundStyle(.primary)
                                if let body = issue.body {
                                    Text(body)
                                        .font(.caption)
                                        .foregroundStyle(.secondary)
                                        .lineLimit(3)
                                }
                            }
                            Spacer()
                            Image(systemName: "arrow.up.right.square")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                        }
                    }
                }
            }

            // Prompt
            if let prompt = card.link.promptBody {
                Section("Prompt") {
                    Text(prompt)
                        .font(.callout)
                        .foregroundStyle(.primary)
                }
            }
        }
    }

    // MARK: - History Placeholder

    private var historyPlaceholder: some View {
        VStack(spacing: 16) {
            Image(systemName: "clock.arrow.circlepath")
                .font(.system(size: 48))
                .foregroundStyle(.secondary)
            Text("Session History")
                .font(.headline)
                .foregroundStyle(.secondary)
            Text("Connect to a Mac running Kanban Code\nto view session transcripts.")
                .font(.caption)
                .foregroundStyle(.tertiary)
                .multilineTextAlignment(.center)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color.gray.opacity(0.1))
    }

    // MARK: - Actions Tab

    private var actionsView: some View {
        List {
            Section {
                Button {
                    copyToClipboard(card.id)
                } label: {
                    Label("Copy Card ID", systemImage: "doc.on.doc")
                }

                if let sessionId = card.link.sessionLink?.sessionId {
                    Button {
                        copyToClipboard("claude --resume \(sessionId)")
                    } label: {
                        Label("Copy Resume Command", systemImage: "terminal")
                    }
                }
            }

            if !card.link.prLinks.isEmpty {
                Section("Pull Requests") {
                    ForEach(card.link.prLinks, id: \.number) { pr in
                        if let urlString = pr.url, let url = URL(string: urlString) {
                            Button {
                                openURL(url)
                            } label: {
                                Label("Open PR #\(pr.number)", systemImage: "arrow.up.right.square")
                            }
                        }
                    }
                }
            }

            if let issue = card.link.issueLink,
               let urlString = issue.url,
               let url = URL(string: urlString) {
                Section("Issue") {
                    Button {
                        openURL(url)
                    } label: {
                        Label("Open Issue #\(issue.number)", systemImage: "arrow.up.right.square")
                    }
                }
            }

            Section {
                Button(role: .destructive) {
                    // Archive
                } label: {
                    Label("Archive Card", systemImage: "archivebox")
                }
            }
        }
    }

    // MARK: - Helpers

    private func prStatusColor(_ status: PRStatus) -> Color {
        switch status {
        case .approved, .reviewNeeded: .green
        case .merged: .purple
        case .closed: .red
        case .pendingCI: .secondary
        case .changesRequested: .orange
        case .failing: .red
        case .unresolved: .orange
        }
    }

    private func openURL(_ url: URL) {
        #if os(iOS)
        UIApplication.shared.open(url)
        #else
        NSWorkspace.shared.open(url)
        #endif
    }

    private func copyToClipboard(_ string: String) {
        #if os(iOS)
        UIPasteboard.general.string = string
        #else
        NSPasteboard.general.clearContents()
        NSPasteboard.general.setString(string, forType: .string)
        #endif
    }
}
