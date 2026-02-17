# my-programming-bitcoin
## 概要
本プロジェクトは、ビットコインのプロトコル内部を深く理解するための学習用リポジトリです。 **汎用的なツールではありません** が、生のバイト列からトランザクションを構築するプロセスを詳細に記録しています。  
※決して、メインネットでブロードキャストするためのトランザクション作成には使用しないでください。  

## ディレクトリ構造  
my-programming-bitcoin/  
├── docs/  
│   ├── modules.md  
│   ├── transaction.md  
├── src/  
│   ├── __init__.py  
│   ├── bech32.py  
│   ├── my_block.py  
│   ├── my_ecc.py  
│   ├── my_helper.py  
│   ├── my_network.py  
│   ├── my_op.py  
│   ├── my_script.py  
│   ├── my_tx.py  
├── .gitignore  
├── main.py  
├── README.md  
├── requirements.txt  

## 実行方法  
```
git clone https://github.com/a-shirakami/my-programming-bitcoin
cd my-programming-bitcoin
python -m venv venv
source venv/bin/activate  # Windowsなら venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## ドキュメント
* [各モジュールの説明](./docs/modules.md)  
  srcフォルダ内の各クラス設計や役割について記載しています。

* [送信したトランザクション](./docs/transaction.md)  
  テストネットで実際に承認されたトランザクションの構造を解説しています。  
