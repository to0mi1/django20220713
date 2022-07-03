import np as np


def leibniz(n):
    """
    ライプニッツ級数を利用して円周率を求める.
    Parameters
    ----------
    n

    Returns
    -------

    """
    x = np.arange(1, n + 1)  # 1~Nまでの自然数の配列
    y = 1 / (2 * x - 1)  # 奇数の逆数の配列を計算
    pm = (-1) ** (x - 1)  # プラマイ１が交互に並ぶ数列の計算
    pi = 4 * np.dot(y, pm)  # yとpmの内積によりプラマイ交互の和を計算し、最後に４をかける


def buffon(process_uuid, mem, result):
    n = 0  # 線に重なる針の本数。初期値０。
    for i in range(mem[0]):  # iが0からN-1までの間、以下を繰り返す。
        # 針の角度のサンプリング。角度を直接サンプルする代わりに単位円内の点をサンプルすることでpiの値依存性を排除。
        r = 2  # サンプル点の原点からの距離。以下のwhile文を行うため初期値を2に。
        while r > 1:  # r<=1となるまでサンプルを繰り返す
            dx = np.random.rand()  # x座標
            dy = np.random.rand()  # y座標
            r = np.sqrt(dx ** 2 + dy ** 2)  # 原点からの距離の計算

        h = 2 * np.random.rand() + dy / r  # 房の先端の高さ（高い方）の計算
        if h > 2:  # 針の先端の高さが平行線の高さを終えた場合
            n += 1  # 線に重なる針の本数を加算
        mem[1] = i + 1
    result.value = mem[0] / n  # 円周率の計算
    # Pi.objects.create(uuid=process_uuid, pi=result.value)
