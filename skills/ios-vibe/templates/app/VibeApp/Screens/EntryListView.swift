import SwiftData
import SwiftUI

/// 主畫面：一份紀錄清單，可以新增一筆、也可以刪掉一筆。
/// 這是範本附的入門畫面，真正的 app 從這裡改。
struct EntryListView: View {
    @Environment(DataSession.self) private var session
    @Environment(\.modelContext) private var modelContext
    @Query(sort: \Entry.createdAt, order: .reverse) private var entries: [Entry]

    @State private var isAddingEntry = false
    @State private var errorMessage: String?

    var body: some View {
        NavigationStack {
            List {
                ForEach(entries) { entry in
                    VStack(alignment: .leading, spacing: 4) {
                        Text(entry.title)
                        Text(entry.createdAt, format: .dateTime.year().month().day().hour().minute())
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    .swipeActions(edge: .trailing) {
                        if !session.isReadOnly {
                            Button("刪除", systemImage: "trash", role: .destructive) {
                                delete(entry)
                            }
                            .accessibilityIdentifier("deleteEntryButton")
                        }
                    }
                }
            }
            .overlay {
                if entries.isEmpty {
                    ContentUnavailableView(
                        "還沒有任何紀錄",
                        systemImage: "tray",
                        description: Text("點右上角的加號新增第一筆。")
                    )
                }
            }
            .navigationTitle("紀錄")
            .safeAreaInset(edge: .top) {
                if let notice = session.notice {
                    NoticeBanner(message: notice.message) {
                        session.dismissNotice()
                    }
                }
            }
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button("新增", systemImage: "plus") {
                        isAddingEntry = true
                    }
                    .disabled(session.isReadOnly)
                    .accessibilityIdentifier("addEntryButton")
                }
            }
            .sheet(isPresented: $isAddingEntry) {
                AddEntryView { title in
                    add(title: title)
                }
            }
            .alert("沒有存成功", isPresented: Binding(get: { errorMessage != nil }, set: { if !$0 { errorMessage = nil } })) {
                Button("好") { errorMessage = nil }
            } message: {
                Text(errorMessage ?? "")
            }
        }
    }

    private func add(title: String) {
        modelContext.insert(Entry(title: title))
        save()
    }

    private func delete(_ entry: Entry) {
        modelContext.delete(entry)
        save()
    }

    /// 明確存檔：使用者一按完就寫進資料庫，app 被關掉也不會掉。
    private func save() {
        do {
            try modelContext.save()
        } catch {
            errorMessage = String(describing: error)
        }
    }
}

private struct NoticeBanner: View {
    let message: String
    let onDismiss: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(message)
                .font(.callout)
            Button("知道了", action: onDismiss)
                .accessibilityIdentifier("dismissNoticeButton")
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding()
        .background(.thinMaterial)
        .accessibilityIdentifier("dataNotice")
    }
}

#Preview {
    let container = try! DataStack.makeInMemoryContainer()
    EntryListView()
        .environment(DataSession(
            container: container,
            files: .preview(),
            isReadOnly: false,
            notice: nil,
            bootstrapper: nil
        ))
        .modelContainer(container)
}
