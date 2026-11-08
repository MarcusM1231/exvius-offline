import SwiftUI

// Explicit isolated launch. Never initializes the normal campaign backend.
struct BannerMenuDiagnostics:View {
    @StateObject private var model=SummonModel()
    @State private var backend:EmbeddedSummonBackend?
    @State private var ready=false
    @State private var status="Preparing isolated menu campaign…"
    private var page:String {
        let a=ProcessInfo.processInfo.arguments
        if let i=a.firstIndex(of:"--menu-page"),a.count>i+1 {return a[i+1]}
        return "menu"
    }
    var body:some View {
        VStack(spacing:0) {
            Text("ISOLATED MENU TEST · "+status).font(.caption2).padding(5).frame(maxWidth:.infinity).background(.purple).foregroundStyle(.white)
            if ready {
                if ["single-confirm","eleven-confirm"].contains(page),let b=model.banners.first,let q=model.menuCatalog?.banners.first(where:{$0.id==b.id})?.offers.first(where:{$0.offer==(page=="single-confirm" ? "primary":"secondary")}) {
                    SummonConfirmation(banner:b,offer:q.transactionOffer,balance:q.balance,busy:true,quote:q,confirm:{})
                } else {
                    GlobalSummonScreen(model:model,refresh:{await refresh()},quote:{b,o in
                        guard let backend else {return nil}
                        return await model.quote(b.id,offer:o.offer,using:backend,identity:"menu-diagnostic")
                    }) { b,o in
                        guard let backend else {return false}
                        return await model.summon(b,offer:o,using:backend,identity:"menu-diagnostic")
                    }
                }
            } else {ProgressView(status).frame(maxWidth:.infinity,maxHeight:.infinity)}
        }.preferredColorScheme(.dark).task {
            do {
                let root=try FileManager.default.url(for:.applicationSupportDirectory,in:.userDomainMask,appropriateFor:nil,create:true)
                    .appendingPathComponent("FFBERevival/validation/menu-"+UUID().uuidString)
                let engine=EmbeddedSummonBackend(storage:root.appendingPathComponent("campaign"));backend=engine
                await model.refresh(using:engine,identity:"menu-diagnostic")
                guard model.menuCatalog != nil,!model.needsRefresh else {throw APIError(message:model.error ?? model.menuError ?? "Menu unavailable")}
                let report:MenuReadOnlyCheck=try await PythonWorker.shared.call(["operation":"menu_diagnostics"])
                guard report.unchanged,report.no_save,report.banners>=469 else {throw APIError(message:"Read-only invariant failed")}
                try JSONEncoder().encode(report).write(to:root.deletingLastPathComponent().appendingPathComponent("banner-menu-report.json"),options:.atomic)
                status="read-only check passed · no normal campaign";ready=true
            } catch {status=error.localizedDescription}
        }
    }
    private func refresh() async {if let backend {await model.refresh(using:backend,identity:"menu-diagnostic")}}
}
private struct MenuReadOnlyCheck:Codable {let unchanged:Bool,no_save:Bool;let banners:Int;let save_sha256:String}
