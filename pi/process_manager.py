import logging
import threading
import time
import uuid
from datetime import datetime
from multiprocessing import Process, Value, Array

from Asobi.pi_calcuater import buffon

logger = logging.getLogger(__name__)


class ProcessManager(object):
    """
    計算プロセスを管理するシングルトンなクラス.

    シングルトンはアプリケーション内で唯一のインスタンスしか持たないクラス.
    プロセスはアプリケーション全体で管理するためこの仕組みが必要.
    """
    __instance = None
    __processes = []
    __lock = threading.Lock()
    __process_watcher = None
    __time_out = 60 * 2

    def __new__(cls):
        """
        シングルトンなインスタンスを生成する.
        """
        # クラスの新しいインスタンスを作るために呼び出される
        # https://docs.python.org/ja/3/reference/datamodel.html#object.__new__
        if cls.__instance is not None:
            # インスタンスが既に存在するときには既にあるインスタンスを返却する
            return cls.__instance
        else:
            # インスタンスを作成前の場合はスーパークラスの __new__ を呼び出す
            inst = cls.__instance = super().__new__(cls)
            # inst.start_process_watcher()
            return inst

    def __init__(self):
        """
        コンストラクタ

        プロセスを定期的に監視するスレッドを生成及び開始する.
        """
        super(ProcessManager, self).__init__()
        # プロセスを監視するメソッドを起動する
        self.start_process_watcher()

    def start_process_watcher(self):
        """
        プロセスの管理状態を定期的に監視するスレッドを立ち上げる.

        Returns
        -------

        """
        # プロセスの監視スレッドはアプリケーション内で１つだけ起動する
        # これはユーザー(セッション)等の単位ではなく、アプリケーションないで起動と状態を管理したいため
        if self.__process_watcher is None:
            # クラスはシングルトンなので、インスタンス変数はアプリケーション全体で使われる
            # インスタンス変数が None の場合はアプリケーション起動直後で監視プロセスが起動していない状態
            # 初回のみこの if 文が真と判定され以下の処理が実行される

            # プロセスを監視するスレッドをインスタンス化し、自クラスのインスタンス変数に格納
            self.__process_watcher = ProcessWatcher()
            # スレッドを起動
            self.__process_watcher.start()

    def watch_process(self) -> bool:
        """
        現在起動しているプロセスを取得し、新たにプロセスを起動可能か評価する.

        Returns
        -------
        is_ready : bool
            プロセスが起動可能であれば True を返却する.
        """
        # TODO 未実装
        return True

    def start_process(self):
        """
        計算プロセスを開始する.

        Returns
        -------

        """
        # 複数のクライアントがプロセスの起動を要求することを想定するため、同時に起動することを抑止するために Lock する.
        # プロセスを管理するためのリストや起動前チェックなどが同時に呼び出される事により想定より多くのプロセスが起動されることを防ぐ
        with self.__lock:
            # 処理結果と処理進捗は Web からもアクセスしたいため共有メモリを作成する
            # https://docs.python.org/ja/3/library/multiprocessing.html#multiprocessing.Value
            # 今回は円周率を求めるため浮動小数点数を型に指定する
            # 型は型コードで指定する
            # https://docs.python.org/ja/3/library/array.html#module-array
            result = Value('d', 0.0)

            # プログレスはプロセス内で反復して行われる処理があるため、(現在の反復回数 / 全反復回数 * 100) の百分率で求める
            # 今回は最初に反復回数は決め打ちのため、配列の0番目に全反復回数、1番目に現在の反復回数を格納するよう設計する
            # 反復回数は起動されるプロセス側で更新するため、Web アプリ側はそれを読み取り進捗を算出する
            # https://docs.python.org/ja/3/library/multiprocessing.html#multiprocessing.Array
            progress = Array('i', [10000000, 0])

            # クライアントが要求したプロセス起動を一意に識別するため、ランダムな値を採番し記憶する
            # 進捗や結果がどの要求に対したものかをこの値で識別する
            # そのため、View や ブラウザでもこの値を利用して識別する
            # https://docs.python.org/ja/3/library/uuid.html#uuid.UUID
            process_uuid = uuid.uuid4()

            # プロセスのインスタンス化
            # プロセスの処理が定義された関数とその関数に渡す変数を指定する
            # 今回は Web アプリケーション側から渡す値が全てプロセスで更新され、
            # Web アプリケーションで参照するため共有メモリでラップして変数を渡す
            # https://docs.python.org/ja/3/library/multiprocessing.html#multiprocessing.Process
            p = Process(target=buffon, args=(progress, result))
            p.start()

            # プロセスを管理するインスタンス変数のリストにプロセス情報を格納する
            self.__processes.append({
                'id': process_uuid.hex,
                'process': p,
                'progress': progress,
                'result': result,
                'start_time': datetime.now()
            })
        return process_uuid.hex, p.pid

    def get_progress(self):
        """
        各プロセスの進捗を取得する.

        Returns
        -------
        processes : doc
            管理中のプロセスの状態を辞書で返却する.
        """
        if len(self.__processes) < 1:
            return []

        return [{
            'id': d['id'],
            'pid': d['process'].pid,
            'progress': d['progress'][1] / d['progress'][0] * 100,
            # 共有メモリ Value を参照／更新するときは value プロパティを利用する
            'result': d['result'].value
        } for d in self.__processes]

    def kill_process(self, proc_id):
        """
        管理中のプロセスを強制終了する.

        Parameters
        ----------
        proc_id : str
            強制終了対象のプロセスのシステム固有ID

        Returns
        -------

        """
        if len(self.__processes) < 1:
            return

        # ユーザーからの要求でプロセスを終了する
        for proc in self.__processes:
            # 管理中のプロセスを全走査し、終了対象のプロセスの管理IDと一致するプロセスを見つける
            if proc['id'] == proc_id:
                # 該当するプロセスが存在したら現在の起動状態をチェックする
                # https://docs.python.org/ja/3/library/multiprocessing.html#multiprocessing.Process.is_alive
                if proc['process'].is_alive():
                    # プロセスが実行中であれば終了する

                    # 終了処理
                    # 終了方法は2種類あるがユーザーの要求により終了する場合は terminate を利用する
                    proc['process'].terminate()

    def cleanup(self):
        """
        管理中のプロセスのうち開始から一定時間以上経過したプロセスを開放する.
        実行中に関わらず開放する.

        Returns
        -------

        """
        # プロセス起動後一定時間経過したプロセスを破棄する
        # 計算中にブラウザを閉じたりログアウトしたときにプロセスのみが生き残ってしまう可能性があるので
        # 任意のタイムアウト時間を設定し、起動後その時間が経過した場合はプロセスを破棄
        with self.__lock:
            if len(self.__processes) < 1:
                # プロセスを管理するリストに値が存在しない時は既に完了済み
                # または起動はしたがそのプロセスが開放されていたとき
                logger.info("管理されているプロセスはありません。")
                return
            logger.info(f"管理されているプロセスが{len(self.__processes)}件あります。")
            for proc in self.__processes:
                # 管理されているプロセス全てをチェック
                # プロセス起動後の時間を計測するため、現在時刻と起動時間を取得
                start_time = proc['start_time']
                # datetime 同士を計算すると timedelta が取得できる
                # https://docs.python.org/ja/3/library/uuid.html#uuid.UUID
                td = datetime.now() - start_time

                # 起動後一定時間以上経過していたら対象のプロセスに対して操作する
                if td.total_seconds() > self.__time_out:
                    pid = proc['process'].pid  # ログ出力のため
                    try:
                        # 起動後実行中であるうちは True が返る
                        if proc['process'].is_alive():
                            # もしかして実行中であればプロセスを強制終了
                            # https://docs.python.org/ja/3/library/multiprocessing.html#multiprocessing.Process.is_alive
                            proc['process'].kill()  # よりの時は寄り強い機能で強制数量する
                        # プロセスが終了済みであればプロセスを開放する
                        # 実行中のまま close すると実行中のプロセスが放置される?
                        proc['process'].close()
                        logger.info(f"プロセスを開放しました。プロセスが終了していない可能性があります。(pid={pid})")
                    except ValueError:
                        # 実行中のプロセスを開放すると例外が発生する
                        # os コマンドで kill する必要があるかもしれない
                        # https://docs.python.org/ja/3/library/subprocess.html#subprocess.run
                        # Windows: https://xtech.nikkei.com/it/atcl/column/15/042000103/080600059/
                        # Linux: https://atmarkit.itmedia.co.jp/ait/articles/1604/05/news022.html
                        # Qiita: https://qiita.com/bluesDD/items/43a255bcf0dee6798967
                        logger.info(f"実行中のプロセスを開放しました。(pid={pid})")
                    self.__processes.remove(proc)


class ProcessWatcher(threading.Thread):
    """
    プロセスをの開放を定期的に実行するスレッド.
    """
    # 何秒毎にプロセスを確認するかの設定
    _sleep_time = 10

    def __init__(self):
        super(ProcessWatcher, self).__init__()

    def run(self) -> None:
        # プロセスマネージャーのインスタンスを得る
        pm = ProcessManager()
        logger.debug("プロセスの監視を開始します。")
        while True:
            pm.cleanup()
            logger.info(f"プロセスのクリーンアップを完了しました。{self._sleep_time}秒待機します。")
            # すごい勢いでチェックしてもしょうがないので、一定時間待機し一定の間隔でチェックする
            time.sleep(self._sleep_time)
