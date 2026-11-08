import SwiftUI
import CryptoKit

struct UnitAnimationEntry: Decodable, Identifiable {
    let master_id: String
    let name: String
    let supported: [String]
    let unsupported: [String:String]?
    let reason: String
    let is_target: Bool
    var id: String {master_id}
}
enum UnitAnimationLibrary {
    static let entries: [UnitAnimationEntry] = {
        do {
            guard let root=Bundle.main.resourceURL?.appendingPathComponent("UnitAnimations") else {return []}
            let receipt=try JSONSerialization.jsonObject(with:Data(contentsOf:root.appendingPathComponent("receipt.json"))) as? [String:Any]
            let data=try Data(contentsOf:root.appendingPathComponent("coverage.json"))
            guard data.count<2_000_000,receipt?["lock_sha256"] as? String == UnitAnimationClip.expectedLock,
                  let files=receipt?["files"] as? [String:String],files["coverage.json"] == SHA256.hash(data:data).map({String(format:"%02x",$0)}).joined() else {return []}
            return try JSONDecoder().decode([String:UnitAnimationEntry].self,from:data).values.sorted {$0.master_id<$1.master_id}
        } catch {return []}
    }()
}
struct UnitAnimationGallery: View {
    @State private var search=""
    var filtered:[UnitAnimationEntry] {UnitAnimationLibrary.entries.filter {search.isEmpty || $0.master_id.contains(search) || $0.name.localizedCaseInsensitiveContains(search)}}
    var body: some View {
        List {
            NavigationLink("Developer action / sequence comparison") { UnitActionResearchView() }
            Section {
                let targets=UnitAnimationLibrary.entries.filter(\.is_target)
                let supported=targets.filter {$0.supported.contains("idle")}.count
                Text("\(supported) supported exact IDs / \(targets.count) target IDs")
                Text("\(String(format:"%.1f",Double(supported)/Double(max(1,targets.count))*100))% idle coverage · finite attack → idle when supported").font(.caption)
                Text("\(targets.filter {$0.supported.contains("atk")}.count) target IDs with validated attacks").font(.caption)
                Text("Includes the 423 target IDs and two preserved research forms. No campaign access or Lapis cost.").font(.caption)
            }
            ForEach(filtered) {entry in
                NavigationLink {UnitAnimationPreview(masterID:entry.master_id)} label: {
                    VStack(alignment:.leading) {
                        Text(entry.name);Text(entry.master_id).font(.caption).monospacedDigit()
                        Text(entry.supported.isEmpty ? entry.reason : entry.supported.joined(separator:", ")).font(.caption).foregroundStyle(.secondary)
                    }
                }
            }
        }.navigationTitle("Original unit animations").searchable(text:$search,prompt:"Name or exact master ID")
    }
}
