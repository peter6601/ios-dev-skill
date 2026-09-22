import SwiftUI

@main
struct VibeAppApp: App {
    @State private var launch = AppLaunch.start()

    var body: some Scene {
        WindowGroup {
            RootView(launch: launch)
        }
    }
}
