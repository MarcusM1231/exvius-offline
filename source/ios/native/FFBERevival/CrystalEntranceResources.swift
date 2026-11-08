import SwiftUI
import CryptoKit
import UIKit

enum CrystalEntranceResources {
    static var directory: URL? { Bundle.main.resourceURL?.appendingPathComponent("CrystalEntrance") }
    static let lockHash = "9d3a21a58820047b6afea966a286ab5b3bc56839583466c9dc5b29c060575a86"
    static func load(_ root: URL?) throws -> [String: UIImage] {
        guard let root else { throw CocoaError(.fileNoSuchFile) }
        let receipt = try JSONSerialization.jsonObject(with: Data(contentsOf: root.appendingPathComponent("receipt.json"))) as? [String: Any]
        guard receipt?["lock_sha256"] as? String == lockHash,
              let files = receipt?["files"] as? [String: String],Set(files.keys) == ["cloud.png","touchscreen.png"] else { throw CocoaError(.fileReadCorruptFile) }
        var result: [String: UIImage] = [:]
        for (name,hash) in files {
            let data = try Data(contentsOf: root.appendingPathComponent(name))
            guard data.count < 2*1024*1024,
                  SHA256.hash(data: data).map({ String(format: "%02x",$0) }).joined() == hash,
                  let image = UIImage(data: data) else { throw CocoaError(.fileReadCorruptFile) }
            result[String(name.dropLast(4))] = image
        }
        return result
    }
}
struct CrystalTouchPrompt: View {
    @ObservedObject var controller: CrystalReconstructionController
    var body: some View {
        Group {
            if controller.showsTouchPrompt {
                Group {
                    if let image = controller.touchPromptImage {
                        // Preserved shared-effect pixels read TOUCH SCREEN.
                        Image(uiImage: image).resizable().scaledToFit().frame(width: 145,height: 145)
                    } else {
                        Text("TOUCH SCREEN").font(.system(size: 27,weight: .semibold,design: .serif)).tracking(2)
                            .foregroundStyle(.white).shadow(color: .blue,radius: 5)
                    }
                }.opacity(0.72+0.24*(1+sin((controller.productionMotionTime ?? 0)*2.0))/2)
                    .accessibilityLabel("TOUCH SCREEN").accessibilityIdentifier("touch-screen-prompt")
            }
        }.allowsHitTesting(false)
    }
}
