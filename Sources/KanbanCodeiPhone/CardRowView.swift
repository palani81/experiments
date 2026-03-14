import SwiftUI
import KanbanCodeCore

struct CardRowView: View {
    let card: KanbanCodeCard
    let isSelected: Bool
    var onSelect: () -> Void = {}

    var body: some View {
        VStack(alignment: .leading, spacing: 6) {
            // Title
            Text(card.displayTitle)
                .font(.body)
                .fontWeight(.medium)
                .lineLimit(2)
                .foregroundStyle(.primary)

            // Project + branch
            HStack(spacing: 6) {
                if let projectName = card.projectName {
                    Label(projectName, systemImage: "folder")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
                if let branch = card.link.worktreeLink?.branch {
                    Label(branch, systemImage: "arrow.triangle.branch")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                        .lineLimit(1)
                }
            }

            // Bottom row: label + time + badges
            HStack(spacing: 6) {
                CardLabelBadge(label: card.link.cardLabel)

                Text(card.relativeTime)
                    .font(.caption2)
                    .foregroundStyle(.tertiary)

                Spacer()

                CardBadgesRow(card: card)
            }
        }
        .padding(12)
        .background(
            isSelected ? Color.accentColor.opacity(0.12) : Color.gray.opacity(0.1),
            in: RoundedRectangle(cornerRadius: 10)
        )
        .overlay(
            RoundedRectangle(cornerRadius: 10)
                .stroke(
                    isSelected ? Color.accentColor.opacity(0.3) : Color.clear,
                    lineWidth: 1
                )
        )
        .contentShape(Rectangle())
        .onTapGesture { onSelect() }
        .contextMenu {
            contextMenuItems
        }
    }

    @ViewBuilder
    private var contextMenuItems: some View {
        if card.column == .backlog {
            Button {
                // Start action would be handled by parent
            } label: {
                Label("Start", systemImage: "play.fill")
            }
        }

        Button {
            copyToClipboard(card.id)
        } label: {
            Label("Copy Card ID", systemImage: "doc.on.doc")
        }

        if let pr = card.link.prLink, let urlString = pr.url,
           let url = URL(string: urlString) {
            Button {
                openURL(url)
            } label: {
                Label("Open PR #\(pr.number)", systemImage: "arrow.up.right.square")
            }
        }

        if let issue = card.link.issueLink,
           let urlString = issue.url,
           let url = URL(string: urlString) {
            Button {
                openURL(url)
            } label: {
                Label("Open Issue #\(issue.number)", systemImage: "arrow.up.right.square")
            }
        }

        Divider()

        Button(role: .destructive) {
            // Archive action handled by parent
        } label: {
            Label("Archive", systemImage: "archivebox")
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

// MARK: - Card Label Badge

struct CardLabelBadge: View {
    let label: CardLabel
    @Environment(\.colorScheme) private var colorScheme

    var body: some View {
        Text(label.rawValue)
            .font(.system(size: 9, weight: .bold, design: .rounded))
            .foregroundStyle(colorScheme == .dark ? .black : .white)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(color, in: Capsule())
    }

    private var color: Color {
        switch label {
        case .session: .orange
        case .worktree: .green
        case .issue: .blue
        case .pr: .purple
        case .task: .gray
        }
    }
}

// MARK: - Card Badges Row

struct CardBadgesRow: View {
    let card: KanbanCodeCard

    var body: some View {
        HStack(spacing: 6) {
            // Terminal indicator
            if card.link.tmuxLink != nil {
                HStack(spacing: 2) {
                    Image(systemName: "terminal")
                        .font(.caption2)
                        .foregroundStyle(.green)
                    if let tmux = card.link.tmuxLink, tmux.terminalCount > 1 {
                        Text(verbatim: "\(tmux.terminalCount)")
                            .font(.system(size: 9, weight: .bold))
                            .foregroundStyle(.green)
                    }
                }
            }

            // PR badge
            if let primary = card.link.prLink {
                PRBadgeView(
                    status: card.link.worstPRStatus,
                    prNumber: primary.number
                )
                if card.link.prLinks.count > 1 {
                    Text(verbatim: "+\(card.link.prLinks.count - 1)")
                        .font(.system(size: 9, weight: .medium))
                        .foregroundStyle(.secondary)
                }
            }

            // Issue indicator
            if let issue = card.link.issueLink {
                HStack(spacing: 2) {
                    Image(systemName: "circle.circle")
                        .font(.caption2)
                    Text(verbatim: "\(issue.number)")
                        .font(.caption2)
                }
                .foregroundStyle(.secondary)
            }

            // Remote indicator
            if card.link.isRemote {
                Image(systemName: "cloud")
                    .font(.caption2)
                    .foregroundStyle(.teal)
            }
        }
    }
}

// MARK: - PR Badge

struct PRBadgeView: View {
    let status: PRStatus?
    let prNumber: Int

    var body: some View {
        HStack(spacing: 3) {
            Image(systemName: statusIcon)
                .font(.system(size: 8))
            Text("#\(prNumber)")
                .font(.system(size: 9, weight: .medium))
        }
        .padding(.horizontal, 5)
        .padding(.vertical, 2)
        .background(Capsule().fill(statusColor.opacity(0.15)))
        .foregroundStyle(statusColor)
    }

    private var statusIcon: String {
        switch status {
        case .approved: "hand.thumbsup.fill"
        case .merged: "checkmark.circle.fill"
        case .closed: "xmark.circle.fill"
        case .pendingCI: "pencil.circle"
        case .changesRequested: "exclamationmark.triangle.fill"
        case .reviewNeeded: "eye.circle"
        case .failing: "xmark.octagon.fill"
        case .unresolved: "questionmark.circle"
        case nil: "questionmark.circle"
        }
    }

    private var statusColor: Color {
        switch status {
        case .approved, .reviewNeeded: .green
        case .merged: .purple
        case .closed: .red
        case .pendingCI: .secondary
        case .changesRequested: .orange
        case .failing: .red
        case .unresolved: .orange
        case nil: .secondary
        }
    }
}
