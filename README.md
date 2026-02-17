# my-programming-bitcoin
## 概要
本プロジェクトは、ビットコインのプロトコル内部を深く理解するための学習用リポジトリです。 **汎用的なツールではありません** が、生のバイト列からトランザクションを構築するプロセスを詳細に記録しています。  
※決して、メインネットでブロードキャストするためのトランザクション作成には使用しないでください。  

## 実行方法  
```
git clone https://github.com/a-shirakami/my-programming-bitcoin.git
python -m venv venv
source venv/bin/activate  # Windowsなら venv\Scripts\activate
pip install -r requirements.txt
```

## 詳細
* [各モジュールの説明](./docs/modules.md)  
  srcフォルダ内の各モジュールの簡単な説明を記載しています。

* [送信したトランザクション](./docs/transaction.md)  
  実際に送信したトランザクションを解説しています。  
