import SwiftUI

/// 新增一筆紀錄的小表單。
struct AddEntryView: View {
    let onSave: (String) -> Void

    @Environment(\.dismiss) private var dismiss
    @State private var title = ""

    private var trimmedTitle: String {
        title.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    var body: some View {
        NavigationStack {
            Form {
                TextField("標題", text: $title)
                    .accessibilityIdentifier("entryTitleField")
            }
            .navigationTitle("新增紀錄")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("取消") { dismiss() }
                        .accessibilityIdentifier("cancelEntryButton")
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("儲存") {
                        onSave(trimmedTitle)
                        dismiss()
                    }
                    .disabled(trimmedTitle.isEmpty)
                    .accessibilityIdentifier("saveEntryButton")
                }
            }
        }
    }
}

#Preview {
    AddEntryView { _ in }
}
