import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render

from pi.process_manager import ProcessManager

logger = logging.getLogger(__name__)


@login_required
def index(request):
    """
    計算画面をレンダリングする

    Parameters
    ----------
    request : WSGIRequest
        Webリクエスト
    Returns
    -------

    """
    logger.debug("index called")
    return render(request, 'pi/index.html', context={})


@login_required
def calc_pi(request):
    """
    円周率の計算を実行する
    Parameters
    ----------
    request : WSGIRequest
        Webリクエスト
    Returns
    -------
    json : JsonResponse
        実行情報 (プロセスの識別ID と OSで管理されたプロセスIDを含む)
    """
    logger.debug("calc_pi called")
    # プロセスマネジャーのインスタンスを得る
    pm = ProcessManager()
    # プロセスの起動命令
    process_uuid, pid = pm.start_process()

    # ユーザーが起動したプロセスの識別情報は session で保持する
    if 'pi' not in request.session:
        # セッションに管理するキーが存在しないときはリストで作成する
        request.session['pi'] = []
    # セッションにプロセスの識別IDを格納
    request.session['pi'].append(process_uuid)

    # JSONでブラウザへレスポンス
    return JsonResponse({
        'id': process_uuid,
        'pid': pid,
    })


@login_required
def progress_pi(request):
    """
    プロセスの進捗情報を取得する.

    Parameters
    ----------
    request
        Webリクエスト

    Returns
    -------
    json : JsonResponse
        現在実行中のプロセスの進捗情報
    """
    # 実行要求したプロセスが無い場合はそのまま空のオブジェクトを JSON でレスポンス
    if 'pi' not in request.session or len(request.session['pi']) < 1:
        return JsonResponse({})
    logger.debug(ProcessManager().get_progress())
    # 実行要求したプロセスが存在するときは、プロセスマネージャーより進捗情報を取得してレスポンスする
    # TODO これだとアプリケーション全体で実行中のプロセスの進捗情報をレスポンスしている
    #  実際は session に格納した 識別ID を使ってそのユーザーが要求したプロセスに限定した方が良い
    #  プロセスマネージャは識別IDを含んだ辞書を返却するため、その情報とセッションの情報を比較しフィルタリングする
    return JsonResponse({'progresses': ProcessManager().get_progress()})


@login_required
def kill_pi(request):
    """
    プロセスの強制終了を要求する.

    Parameters
    ----------
    request
        Webリクエスト.
        body に 強制終了するプロセスの識別IDを指定する.
    Returns
    -------
        json : JsonResponse
            空のオブジェクト
    """
    # 実行要求履歴が無い場合は処理をしない
    if 'pi' not in request.session or len(request.session['pi']) < 1:
        return JsonResponse({})
    # HTTPリクエストのボディから JSON 文字列を読み込み、Python オブジェクトへ変換する
    data = json.loads(request.body)
    logger.debug(ProcessManager().get_progress())
    # body から強制終了対象の識別IDを取得し、プロセスマネージャーに終了要求をする
    # TODO このとき、JSON に識別IDが含まれない可能性があるので、id を辞書に含むかチェックをする必要がある
    ProcessManager().kill_process(data['id'])
    return JsonResponse({})
