# -*- coding: utf-8 -*-
import http.server
import socketserver
import os
import urllib.parse
import sys
import threading
from functools import partial

# サーバーを起動するポート番号を設定します。
# 8000は一般的によく使われるポートです。
PORT = 8000

# コマンドライン引数からディレクトリを取得します。
# パスが指定されなかった場合は、プログラムを終了します。
if len(sys.argv) > 1:
    DIRECTORY = sys.argv[1]
    if not os.path.isdir(DIRECTORY):
        print(f"エラー: 指定されたパス '{DIRECTORY}' はディレクトリではありません。")
        sys.exit(1)
else:
    print("エラー: サーバーを起動するディレクトリを指定してください。")
    print(f"使い方: python {os.path.basename(__file__)} <directory_path>")
    sys.exit(1)


class Handler(http.server.SimpleHTTPRequestHandler):
    """
    http.server.SimpleHTTPRequestHandlerを継承して、
    ディレクトリの一覧をカスタマイズするハンドラーです。
    """
    def list_directory(self, path):
        """
        ディレクトリの中身をリスト表示する機能を上書きします。
        IEでも表示できるように、より互換性の高いHTMLを生成します。
        """
        try:
            # os.listdirでディレクトリの中身を取得し、ソートします。
            list_of_files = sorted(os.listdir(path))
        except OSError:
            # ディレクトリの読み込みに失敗した場合のエラー処理
            self.send_error(404, "No permission to list directory")
            return None

        # HTMLのヘッダーを作成します。
        # IEでも正しく表示されるように、HTML4.01 StrictのDOCTYPEを使用します。
        title = "Directory listing for %s" % self.path
        encoded_title = title.encode('utf-8', 'surrogateescape').decode('utf-8')
        html_content = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">'
        html_content += '<html>'
        html_content += '<head>'
        html_content += '<meta http-equiv="Content-Type" content="text/html; charset=utf-8">'
        html_content += '<title>%s</title>' % encoded_title
        html_content += '<style>'
        html_content += 'body { font-family: "Segoe UI", sans-serif; margin: 2rem; }'
        html_content += 'ul { list-style-type: none; padding: 0; }'
        html_content += 'li { margin-bottom: 0.5rem; }'
        html_content += 'a { text-decoration: none; color: #0078D4; }'
        html_content += 'a:hover { text-decoration: underline; }'
        html_content += '</style>'
        html_content += '</head>'
        html_content += '<body>'
        html_content += '<h1>%s</h1>' % encoded_title
        html_content += '<ul>'

        # 親ディレクトリへのリンクを追加
        html_content += '<li><a href="%s">%s</a></li>' % (urllib.parse.quote('..', safe=''), '..')

        # 各ファイルとフォルダのリストを作成します。
        for name in list_of_files:
            # ファイル名をURLエンコードします。
            displayname = linkname = name
            path_for_link = os.path.join(path, name)
            if os.path.isdir(path_for_link):
                displayname = name + "/"
                # quote()関数の引数の渡し方を修正
                linkname = urllib.parse.quote(name, encoding='utf-8', safe='/') + '/'
            else:
                # quote()関数の引数の渡し方を修正
                linkname = urllib.parse.quote(name, encoding='utf-8', safe='/')
            
            html_content += '<li><a href="%s">%s</a></li>' % (linkname, displayname)

        # HTMLのフッターを作成します。
        html_content += '</ul>'
        html_content += '</body>'
        html_content += '</html>'

        # レスポンスとしてHTMLを送信します。
        encoded_content = html_content.encode('utf-8')
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded_content)))
        self.end_headers()
        self.wfile.write(encoded_content)

        return None

# サーバーの設定
# functools.partialを使って、HandlerにDIRECTORYを渡せるようにします。
Handler_with_directory = partial(Handler, directory=DIRECTORY)
# ThreadingTCPServerを使用して、各リクエストを別のスレッドで処理します。
with socketserver.ThreadingTCPServer(("", PORT), Handler_with_directory) as httpd:
    print(f"サーバーを起動しました。ポート番号: {PORT}")
    print(f"公開ディレクトリ: {os.path.abspath(DIRECTORY)}")
    print(f"以下のURLをブラウザで開いてください: http://localhost:{PORT}")
    print(f"サーバーを停止するには、Ctrl + C を押してください。")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーをシャットダウンしています...")
    finally:
        httpd.server_close()
        print("サーバーは正常に停止しました。")
