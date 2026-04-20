from chm_to_markdown import CHMConverter

def test_conversion():
    converter = CHMConverter()
    
    html = """
    <html>
    <head><title>Test</title><style>.hidden { display: none; }</style></head>
    <body>
        <h1>Title</h1>
        <p>This is a <a href="link.html">link</a> and some text.</p>
        <div class="code">Dim x As Integer</div>
        <table>
            <tr><th>Header 1</th><th>Header 2</th></tr>
            <tr><td>Val 1</td><td>Val 2 | with pipe</td></tr>
        </table>
        <script>alert('bad');</script>
        <h2>SubTitle</h2>
        <pre>MsgBox "Hello"</pre>
    </body>
    </html>
    """
    
    md = converter.html_to_markdown(html, "TestSection")
    print("--- Generated Markdown ---")
    print(md)
    print("--------------------------")

    # Basic assertions
    assert "# Section: TestSection" in md
    assert "# Title" in md
    assert "**link**" in md
    assert "```vb\nDim x As Integer" in md
    assert "| Header 1 | Header 2 |" in md
    assert "| Val 1 | Val 2 \\| with pipe |" in md
    assert "alert('bad')" not in md
    assert "## SubTitle" in md
    assert "```vb\nMsgBox \"Hello\"" in md
    print("All tests passed!")

if __name__ == "__main__":
    test_conversion()
