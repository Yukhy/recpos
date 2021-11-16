# RECPOS（開発中）

## **アプリケーション概要**

- 就活者向けのメールボックスWebアプリケーションです。
- メールボックス機能に加え、自分の気になる企業のリスト化、タスクやイベント情報の管理が本アプリケーション内で行なえます。
- Googleアカウントで本アプリケーションにログインすることで利用できます。

## **URL**

- 未デプロイ

## デモページ

- 未デプロイ

## 開発の目的

- 就職活動中に得られる情報を一元管理し、ユーザーの情報過多による煩わしさを軽減するため。

## 開発に使用した主な技術

- Python 3.9.7
- Django 3.2.8
- Gmail API v1
- Bootstrap 5.1

## **実装した機能**

- Mailbox
    - Inbox
        - デフォルトの動作
            - Googleアカウントのメールアドレスで受信したメールを取得、閲覧、スター付け、削除できます。
        - エイリアスのメールアドレスを登録した際の動作
            - エイリアスのメールアドレスで受信したメールを取得、閲覧、スター付け、削除できます。
    - Star
        - デフォルトの動作
            - スター付けされたメールを取得、閲覧、スター外し、削除できます。
        - エイリアスのメールアドレスを登録した際の動作
            - エイリアスのメールアドレス内でスター付けされたメールを取得、閲覧、スター外し、削除できます。
- RECPOS Extensions
    - Company List
        - 本アプリケーション内でユーザーが登録した企業を一覧することができます。
            - 企業ごとにフィルタリングされたのメモ
            - 企業ごとにフィルタリングされたタスク、イベント
    - My Tasks
        - 本アプリケーション内でユーザーが登録したタスク、イベントをカレンダーベースで閲覧できます。

## **実装予定の機能**

- メールの送信機能

## **データベース設計**

![RECPOS_db.png](https://s3.us-west-2.amazonaws.com/secure.notion-static.com/6ef8d6dc-60a5-421a-9965-86519ec94170/RECPOS_db.png?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAT73L2G45EIPT3X45%2F20211116%2Fus-west-2%2Fs3%2Faws4_request&X-Amz-Date=20211116T133134Z&X-Amz-Expires=86400&X-Amz-Signature=65de68e2f146f0a67f84ac24dc58726efc2501016f6f66a6cc76a9d718d77f24&X-Amz-SignedHeaders=host&response-content-disposition=filename%20%3D%22RECPOS_db.png%22)

## **ローカルでの動作方法**

（事前にrequirements.txtから必要なライブラリをインストールしてください。）

1. `git clone [https://github.com/Yukhy/recpos.git](https://github.com/Yukhy/recpos.git)`
2. config/setting.pyにSECRET_KEYとrefresh_tokenを挿入
    1. refresh_tokenはGoogle Cloud Platformで立ち上げたアプリケーションのトークンです。
3. `python [manage.py](http://manage.py) makemigrations`
4. `python [manage.py](http://manage.py) migrate`
5. `python [manage.py](http://manage.py) runserver`
6. ブラウザで`localhost:8000`にアクセス

## ライセンス事項

- 本アプリケーションで使用したアプリケーションのライセンスはLICENSEを御覧ください。
- 本アプリケーションで使用したライブラリ等のライセンスはlibrary-LICENSEを御覧ください。
