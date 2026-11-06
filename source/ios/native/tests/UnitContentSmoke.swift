import Foundation
import ImageIO

@main
struct UnitContentSmoke {
    static func main() throws {
        let catalog = try UnitCatalog(directory: URL(fileURLWithPath: CommandLine.arguments[1]))
        precondition(catalog.namedCount == 3089 && catalog.artworkCount == 3)
        for (id, name) in [("100004203", "Ludmille"), ("100000102", "Rain"), ("100000202", "Lasswell")] {
            let display = catalog.display(masterID: id, backendName: "Fixture unit", rarity: nil, isAward: false)
            precondition(display.name == name)
            guard let url = display.artworkURL, let source = CGImageSourceCreateWithURL(url as CFURL, nil),
                  let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else { fatalError("Sprite did not decode") }
            precondition(image.width > 0 && image.height > 0)
        }
        let exactForm = catalog.display(masterID: "100004204", backendName: "Ludmille", rarity: 4, isAward: true)
        precondition(exactForm.name == "Ludmille" && exactForm.artworkURL == nil) // Same name, different ID.
        let ownedForm = catalog.display(masterID: "100004204", backendName: nil, rarity: 3, isAward: false)
        precondition(ownedForm.rarity == "Rarity: 4★") // Current form differs from original award rarity.
        let outcome = try JSONDecoder().decode(Award.self,
            from: Data(#"{"instance_id":"copy1","unit_id":"100004203","name":"Fixture unit","granted_rarity":"4"}"#.utf8))
        let result = catalog.display(masterID: outcome.unit_id, backendName: outcome.name,
                                     rarity: outcome.granted_rarity, isAward: true)
        precondition(result.name == "Ludmille" && result.rarity == "Summoned: 4★") // Actual award overrides row rarity.
        precondition(result.metadata == "Base: 3★ · Awakening cap: 5★")
        let unknown = catalog.display(masterID: "missing", backendName: "Ludmille", rarity: nil, isAward: true)
        precondition(unknown.name == "Unknown unit (missing)" && unknown.artworkURL == nil)
        precondition(unknown.rarity == "Summoned: unknown")
        precondition(catalog.artworkURL(masterID: "../../100004203") == nil)
        let owned = try JSONDecoder().decode([UnitRecord].self, from: Data(#"[{"instance_id":"1","master_id":"100004203","level":1,"granted_rarity":"3"},{"instance_id":"2","master_id":"100004203","level":2}]"#.utf8))
        precondition(owned.count == 2 && owned[0].id != owned[1].id)
        precondition(owned[0].granted_rarity == 3 && owned[1].granted_rarity == nil)
        for copy in owned {
            let row = catalog.display(masterID: copy.master_id, backendName: copy.name,
                                      rarity: copy.granted_rarity, isAward: false)
            precondition(row.name == "Ludmille" && row.rarity == "Rarity: 3★")
        }
        let emptyDirectory = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: emptyDirectory, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: emptyDirectory) }
        try FileManager.default.copyItem(at: catalog.directory.appendingPathComponent("catalog.json"),
                                         to: emptyDirectory.appendingPathComponent("catalog.json"))
        let missingFiles = try UnitCatalog(directory: emptyDirectory)
        let missingArt = missingFiles.display(masterID: "100004203", backendName: nil, rarity: 3, isAward: true)
        precondition(missingArt.name == "Ludmille" && missingArt.artworkURL == nil)
        let demoData = Data(#"{"schema":1,"mode":"demo","units":{}}"#.utf8)
        try demoData.write(to: emptyDirectory.appendingPathComponent("catalog.json"))
        let demoCatalog = try UnitCatalog(directory: emptyDirectory)
        precondition(demoCatalog.display(masterID: "100004203", backendName: "Fixture unit 100004203",
                                        rarity: 3, isAward: true).name == "Fixture unit 100004203")
        print("Swift unit display passed: names, rarity, exact-ID PNG decoding, unknowns and duplicate copies")
    }
}
