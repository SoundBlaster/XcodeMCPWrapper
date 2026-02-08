# Usage Examples

## Example 1: Build Project

```
User: Build my project

Agent: I'll build your Xcode project. First, let me check what windows are open.
→ XcodeListWindows()
← { "windows": [{"tabIdentifier": "windowtab1", "workspacePath": "/Users/you/MyApp.xcodeproj"}] }

Agent: I see MyApp.xcodeproj is open. Building now.
→ BuildProject({ "tabIdentifier": "windowtab1" })
← { "buildResult": "success", "elapsedTime": 2.17, "errors": [] }

Agent: ✅ Build successful! Completed in 2.17 seconds with no errors.
```

## Example 2: Read and Edit File

```
User: Read the main view file

Agent: Let me read the main view file for you.
→ XcodeRead({ "tabIdentifier": "windowtab1", "path": "MyApp/ContentView.swift" })
← { "content": "import SwiftUI\n\nstruct ContentView: View {\n    var body: some View {\n        Text(\"Hello\")\n    }\n}" }

User: Change the text to say "Hello World"

Agent: I'll update the text for you.
→ XcodeUpdate({ 
    "tabIdentifier": "windowtab1",
    "path": "MyApp/ContentView.swift",
    "oldString": "Text(\"Hello\")",
    "newString": "Text(\"Hello World\")"
  })
← { "success": true }

Agent: ✅ File updated successfully!
```

## Example 3: Run Tests

```
User: Run my unit tests

Agent: I'll run the unit tests for you.
→ RunAllTests({ "tabIdentifier": "windowtab1" })
← { 
    "testRun": "success",
    "totalTests": 42,
    "passed": 40,
    "failed": 2,
    "duration": 15.3
  }

Agent: ✅ Test run complete!
   - Total: 42 tests
   - Passed: 40
   - Failed: 2
   - Duration: 15.3 seconds
```

## Example 4: Search Documentation

```
User: How do I use SwiftUI List?

Agent: Let me search the Apple documentation for you.
→ DocumentationSearch({ "query": "SwiftUI List" })
← { 
    "results": [
      { "title": "List | Apple Developer Documentation", "url": "..." },
      { "title": "WWDC 2023: Build better lists in SwiftUI", "url": "..." }
    ]
  }

Agent: Here are the most relevant results for SwiftUI List...
```
