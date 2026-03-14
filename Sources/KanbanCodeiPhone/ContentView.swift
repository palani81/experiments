import SwiftUI
import KanbanCodeCore

struct ContentView: View {
    @State private var selectedColumn: KanbanCodeColumn = .inProgress
    @State private var selectedCardId: String?
    @State private var showNewTask = false
    @State private var showSearch = false
    @State private var showSettings = false
    @State private var cards: [KanbanCodeCard] = []
    @State private var isLoading = false
    @State private var searchText = ""
    @State private var error: String?

    // Demo data for initial display
    private let columns: [KanbanCodeColumn] = [
        .backlog, .inProgress, .waiting, .inReview, .done
    ]

    var body: some View {
        NavigationStack {
            VStack(spacing: 0) {
                // Column tab picker
                columnPicker

                // Card list for selected column
                cardListView
            }
            .navigationTitle("Kanban Code")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarLeading) {
                    Button {
                        showSearch = true
                    } label: {
                        Image(systemName: "magnifyingglass")
                    }
                }
                ToolbarItem(placement: .topBarTrailing) {
                    Menu {
                        Button {
                            showNewTask = true
                        } label: {
                            Label("New Task", systemImage: "plus")
                        }
                        Button {
                            showSettings = true
                        } label: {
                            Label("Settings", systemImage: "gear")
                        }
                    } label: {
                        Image(systemName: "ellipsis.circle")
                    }
                }
            }
            .sheet(isPresented: $showNewTask) {
                NewTaskSheet(onAdd: { name, project in
                    addManualTask(name: name, project: project)
                })
            }
            .sheet(isPresented: $showSettings) {
                SettingsSheet()
            }
            .sheet(isPresented: $showSearch) {
                SearchSheet(
                    cards: cards,
                    searchText: $searchText,
                    onSelect: { cardId in
                        selectedCardId = cardId
                        showSearch = false
                        // Switch to the column containing this card
                        if let card = cards.first(where: { $0.id == cardId }) {
                            selectedColumn = card.column
                        }
                    }
                )
            }
            .overlay {
                if let error {
                    errorBanner(error)
                }
            }
        }
        .task {
            await loadSampleData()
        }
        .onReceive(NotificationCenter.default.publisher(for: .kanbanCodeSelectCard)) { notification in
            if let cardId = notification.userInfo?["cardId"] as? String {
                selectedCardId = cardId
                if let card = cards.first(where: { $0.id == cardId }) {
                    selectedColumn = card.column
                }
            }
        }
    }

    // MARK: - Column Picker

    private var columnPicker: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 8) {
                ForEach(columns, id: \.self) { column in
                    let count = cards.filter { $0.column == column }.count
                    Button {
                        withAnimation(.easeInOut(duration: 0.2)) {
                            selectedColumn = column
                        }
                    } label: {
                        HStack(spacing: 4) {
                            Text(column.displayName)
                                .font(.subheadline)
                                .fontWeight(selectedColumn == column ? .semibold : .regular)
                            if count > 0 {
                                Text("\(count)")
                                    .font(.caption2)
                                    .fontWeight(.medium)
                                    .padding(.horizontal, 5)
                                    .padding(.vertical, 1)
                                    .background(
                                        Capsule().fill(
                                            selectedColumn == column
                                                ? Color.white.opacity(0.3)
                                                : Color.secondary.opacity(0.2)
                                        )
                                    )
                            }
                        }
                        .padding(.horizontal, 12)
                        .padding(.vertical, 8)
                        .background(
                            selectedColumn == column
                                ? Color.accentColor
                                : Color(.systemGray5),
                            in: Capsule()
                        )
                        .foregroundStyle(
                            selectedColumn == column ? .white : .primary
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
        }
        .background(Color(.systemBackground))
    }

    // MARK: - Card List

    private var cardListView: some View {
        let columnCards = cards.filter { $0.column == selectedColumn }
            .sorted {
                switch ($0.link.sortOrder, $1.link.sortOrder) {
                case (let a?, let b?): return a < b
                case (_?, nil): return true
                case (nil, _?): return false
                case (nil, nil):
                    let t0 = $0.link.lastActivity ?? $0.link.updatedAt
                    let t1 = $1.link.lastActivity ?? $1.link.updatedAt
                    if t0 != t1 { return t0 > t1 }
                    return $0.id < $1.id
                }
            }

        return Group {
            if columnCards.isEmpty {
                emptyColumnView
            } else {
                List {
                    ForEach(columnCards) { card in
                        CardRowView(
                            card: card,
                            isSelected: card.id == selectedCardId,
                            onSelect: {
                                selectedCardId = selectedCardId == card.id ? nil : card.id
                            }
                        )
                        .listRowInsets(EdgeInsets(top: 4, leading: 16, bottom: 4, trailing: 16))
                        .listRowSeparator(.hidden)
                        .swipeActions(edge: .trailing) {
                            if card.column != .done {
                                Button {
                                    moveCard(card.id, to: .done)
                                } label: {
                                    Label("Done", systemImage: "checkmark")
                                }
                                .tint(.green)
                            }
                            Button(role: .destructive) {
                                archiveCard(card.id)
                            } label: {
                                Label("Archive", systemImage: "archivebox")
                            }
                        }
                        .swipeActions(edge: .leading) {
                            if card.column == .backlog {
                                Button {
                                    moveCard(card.id, to: .inProgress)
                                } label: {
                                    Label("Start", systemImage: "play.fill")
                                }
                                .tint(.blue)
                            }
                        }
                    }
                }
                .listStyle(.plain)
                .refreshable {
                    await loadSampleData()
                }
            }
        }
    }

    private var emptyColumnView: some View {
        VStack(spacing: 12) {
            Image(systemName: columnIcon(for: selectedColumn))
                .font(.largeTitle)
                .foregroundStyle(.secondary)
            Text("No cards in \(selectedColumn.displayName)")
                .font(.headline)
                .foregroundStyle(.secondary)
            if selectedColumn == .backlog {
                Button {
                    showNewTask = true
                } label: {
                    Label("New Task", systemImage: "plus")
                }
                .buttonStyle(.borderedProminent)
                .controlSize(.small)
            }
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(.systemGroupedBackground))
    }

    // MARK: - Error Banner

    private func errorBanner(_ message: String) -> some View {
        VStack {
            Spacer()
            HStack(spacing: 10) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundStyle(.orange)
                Text(message)
                    .font(.footnote)
                    .lineLimit(2)
                Spacer()
                Button("Dismiss") {
                    withAnimation { error = nil }
                }
                .font(.footnote)
                .buttonStyle(.bordered)
                .controlSize(.mini)
            }
            .padding(12)
            .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 12))
            .padding(.horizontal, 16)
            .padding(.bottom, 8)
        }
        .transition(.move(edge: .bottom).combined(with: .opacity))
    }

    // MARK: - Helpers

    private func columnIcon(for column: KanbanCodeColumn) -> String {
        switch column {
        case .backlog: "tray"
        case .inProgress: "play.circle"
        case .waiting: "exclamationmark.circle"
        case .inReview: "eye"
        case .done: "checkmark.circle"
        case .allSessions: "list.bullet"
        }
    }

    // MARK: - Actions

    private func addManualTask(name: String, project: String?) {
        let link = Link(
            name: name,
            projectPath: project,
            column: .backlog,
            source: .manual
        )
        let card = KanbanCodeCard(link: link)
        cards.append(card)
    }

    private func moveCard(_ cardId: String, to column: KanbanCodeColumn) {
        guard let index = cards.firstIndex(where: { $0.id == cardId }) else { return }
        var link = cards[index].link
        link.column = column
        link.updatedAt = .now
        cards[index] = KanbanCodeCard(
            link: link,
            session: cards[index].session,
            activityState: cards[index].activityState
        )
    }

    private func archiveCard(_ cardId: String) {
        cards.removeAll { $0.id == cardId }
    }

    // MARK: - Data Loading

    private func loadSampleData() async {
        guard cards.isEmpty else { return }
        isLoading = true

        // Create sample cards to demonstrate the UI
        let sampleCards: [KanbanCodeCard] = [
            KanbanCodeCard(link: Link(
                name: "Implement user authentication",
                projectPath: "/Users/dev/my-app",
                column: .backlog,
                source: .manual
            )),
            KanbanCodeCard(link: Link(
                name: "Fix login page CSS",
                projectPath: "/Users/dev/my-app",
                column: .backlog,
                source: .githubIssue,
                issueLink: IssueLink(number: 42, url: "https://github.com/example/repo/issues/42")
            )),
            KanbanCodeCard(link: Link(
                name: "Add dark mode support",
                projectPath: "/Users/dev/my-app",
                column: .inProgress,
                source: .discovered,
                sessionLink: SessionLink(sessionId: "session-001"),
                tmuxLink: TmuxLink(sessionName: "kanban-dark-mode"),
                worktreeLink: WorktreeLink(path: "/Users/dev/my-app/.claude/worktrees/dark-mode", branch: "feat/dark-mode")
            )),
            KanbanCodeCard(link: Link(
                name: "Refactor API endpoints",
                projectPath: "/Users/dev/my-app",
                column: .inProgress,
                source: .hook,
                sessionLink: SessionLink(sessionId: "session-002"),
                tmuxLink: TmuxLink(sessionName: "kanban-api-refactor")
            )),
            KanbanCodeCard(link: Link(
                name: "Review: Update dependencies",
                projectPath: "/Users/dev/my-app",
                column: .waiting,
                source: .discovered,
                sessionLink: SessionLink(sessionId: "session-003")
            )),
            KanbanCodeCard(link: Link(
                name: "Database migration script",
                projectPath: "/Users/dev/backend",
                column: .inReview,
                source: .discovered,
                sessionLink: SessionLink(sessionId: "session-004"),
                worktreeLink: WorktreeLink(path: "/Users/dev/backend/.claude/worktrees/db-migration", branch: "feat/db-migration"),
                prLinks: [PRLink(number: 123, url: "https://github.com/example/backend/pull/123", status: .open, title: "Database migration")]
            )),
            KanbanCodeCard(link: Link(
                name: "Setup CI/CD pipeline",
                projectPath: "/Users/dev/my-app",
                column: .done,
                source: .discovered,
                sessionLink: SessionLink(sessionId: "session-005"),
                prLinks: [PRLink(number: 100, status: .merged, title: "CI/CD setup")]
            )),
        ]

        cards = sampleCards
        isLoading = false
    }
}
