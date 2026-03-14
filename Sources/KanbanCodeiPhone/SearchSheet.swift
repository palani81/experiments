import SwiftUI
import KanbanCodeCore

struct SearchSheet: View {
    let cards: [KanbanCodeCard]
    @Binding var searchText: String
    var onSelect: (String) -> Void
    @Environment(\.dismiss) private var dismiss

    private var filteredCards: [KanbanCodeCard] {
        guard !searchText.isEmpty else { return cards }
        let query = searchText.lowercased()
        return cards.filter { card in
            card.displayTitle.lowercased().contains(query) ||
            (card.projectName?.lowercased().contains(query) ?? false) ||
            (card.link.worktreeLink?.branch?.lowercased().contains(query) ?? false) ||
            card.link.cardLabel.rawValue.lowercased().contains(query)
        }
    }

    var body: some View {
        NavigationStack {
            List {
                if filteredCards.isEmpty && !searchText.isEmpty {
                    ContentUnavailableView.search(text: searchText)
                } else {
                    ForEach(filteredCards) { card in
                        Button {
                            onSelect(card.id)
                        } label: {
                            HStack {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(card.displayTitle)
                                        .font(.body)
                                        .foregroundStyle(.primary)
                                        .lineLimit(1)

                                    HStack(spacing: 6) {
                                        CardLabelBadge(label: card.link.cardLabel)

                                        Text(card.column.displayName)
                                            .font(.caption2)
                                            .foregroundStyle(.secondary)

                                        if let project = card.projectName {
                                            Text(project)
                                                .font(.caption2)
                                                .foregroundStyle(.secondary)
                                        }
                                    }
                                }
                                Spacer()
                                Image(systemName: "chevron.right")
                                    .font(.caption)
                                    .foregroundStyle(.tertiary)
                            }
                        }
                    }
                }
            }
            .listStyle(.plain)
            .searchable(text: $searchText, prompt: "Search cards...")
            .navigationTitle("Search")
            #if os(iOS)
            .navigationBarTitleDisplayMode(.inline)
            #endif
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
            }
        }
    }
}
