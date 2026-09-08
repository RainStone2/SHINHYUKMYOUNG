import pygame
import time

# 1. 초기화
pygame.init()

# 2. 화면 설정
screen_width = 1920
screen_height = 1080
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("동물의숲비슷한거")

white = (255, 255, 255)
blue = (0, 0, 255)

running = True
gameStarted = False

startBg = pygame.image.load("img/startingBg.png")
tile_grass = pygame.image.load("img/tile_1.jpeg")

map=[]
sizeW = 300 #타일가로개수
sizeH = 300 #타일세로개수
sizeTemp = []

for i in range(sizeH):
    for j in range(sizeW):
        sizeTemp.append(1)
    map.append(sizeTemp)
    sizeTemp = []
#print(map)

TILE = 60  # 타일 한 칸의 픽셀 크기

# 타일 번호별 색깔
tileColors = {
    0: (70, 130, 200),    # 물
    1: (110, 190, 90),    # 잔디
    2: (210, 190, 130),   # 모래
}
gray = (150, 150, 150)
gridColor = (95, 165, 80)

# 맵 전체 크기(픽셀)
mapPixelW = sizeW * TILE
mapPixelH = sizeH * TILE

# 주인공의 월드 좌표(픽셀). 맵 한가운데에서 시작
playerX = mapPixelW // 2
playerY = mapPixelH // 2
playerSpeed = 300  # 초당 픽셀
playerW = 40
playerH = 56
inventoryOpened = -1 #1= True -1 = False
tradeOpened = -1     #1= True -1 = False

# --- 폰트: 루프 밖에서 딱 한 번만 만든다 (매 프레임 만들면 심하게 느려짐) ---
fontBig   = pygame.font.SysFont("applesdgothicneo", 40)
font      = pygame.font.SysFont("applesdgothicneo", 26)
fontSmall = pygame.font.SysFont("applesdgothicneo", 20)

black     = (30, 30, 30)
panelBg   = (250, 248, 240)
panelLine = (90, 80, 60)
slotBg    = (215, 210, 195)
btnBg     = (120, 190, 120)
upColor   = (220, 60, 60)
downColor = (60, 90, 220)

# --- 아이템 / 인벤토리 ---
itemDefs = {
    "moocoin": {"name": "무트코인", "color": (240, 190, 60), "max": 99},
}
inv = [None] * 10   # 각 칸은 None 이거나 {"id": ..., "count": ...}
bells = 5000


def invCount(itemId):
    """인벤토리 전체에서 해당 아이템의 총 개수"""
    total = 0
    for slot in inv:
        if slot is not None and slot["id"] == itemId:
            total += slot["count"]
    return total


def invSpace(itemId, n):
    """n개를 실제로 넣을 자리가 있는지 검사만 한다 (사기 전에 호출)"""
    stackMax = itemDefs[itemId]["max"]
    room = 0
    for slot in inv:
        if slot is None:
            room += stackMax
        elif slot["id"] == itemId:
            room += stackMax - slot["count"]
    return room >= n


def invAdd(itemId, n):
    """이미 있는 스택부터 채우고, 남으면 빈 칸을 쓴다"""
    stackMax = itemDefs[itemId]["max"]
    for slot in inv:
        if n <= 0:
            break
        if slot is not None and slot["id"] == itemId:
            put = min(stackMax - slot["count"], n)
            slot["count"] += put
            n -= put
    for i in range(len(inv)):
        if n <= 0:
            break
        if inv[i] is None:
            put = min(stackMax, n)
            inv[i] = {"id": itemId, "count": put}
            n -= put
    return n == 0


def invRemove(itemId, n):
    """부족하면 아무것도 건드리지 않고 False를 돌려준다"""
    if invCount(itemId) < n:
        return False
    for i in range(len(inv)):
        if n <= 0:
            break
        slot = inv[i]
        if slot is not None and slot["id"] == itemId:
            take = min(slot["count"], n)
            slot["count"] -= take
            n -= take
            if slot["count"] == 0:
                inv[i] = None   # 다 쓴 칸은 비운다
    return True


# --- 무트코인 시세: 실제 시각만으로 정해지는 순수 함수 ---
SLOT_SECONDS = 300   # 5분마다 가격이 바뀐다


def currentSlot():
    """지금이 몇 번째 5분 구간인지"""
    return int(time.time() // SLOT_SECONDS)


def hash01(n):
    """정수 -> 0.0~1.0. 같은 입력이면 언제나 같은 값 (결정론적 난수)"""
    x = (n * 2654435761) % (2 ** 32)
    x ^= x >> 13
    x = (x * 1274126177) % (2 ** 32)
    x ^= x >> 16
    return x / (2 ** 32)


def mooPrice(slot):
    """슬롯 번호 -> 가격(벨). 주기가 다른 파동 3개를 겹쳐 자연스러운 곡선을 만든다"""
    v = 0.0
    for period, weight in ((24, 0.55), (6, 0.30), (1, 0.15)):
        a = hash01(slot // period)
        b = hash01(slot // period + 1)
        t = (slot % period) / period
        t = t * t * (3 - 2 * t)        # smoothstep: 꺾이는 부분을 부드럽게
        v += (a + (b - a) * t) * weight
    return int(60 + v * 540)           # 60 ~ 600벨


mooSlot = -1   # 마지막으로 계산한 슬롯
mooNow = 0     # 현재가
mooPrev = 0    # 직전 슬롯 가격 (▲▼ 판정용)

#npc는 rect, 위치로 저장
mooW, mooH = 60, 80
mooX = mapPixelW // 2 + 240   # 시작 지점 바로 오른쪽
mooY = mapPixelH // 2
Moo = {
    "name": "무",
    "pos": [mooX, mooY],
    "rect": pygame.Rect(mooX - mooW // 2, mooY - mooH // 2, mooW, mooH),
}
INTERACT_RANGE = 70

# 거래창: 그리기와 클릭 판정이 같은 rect를 쓰도록 미리 정의
tradePanel = pygame.Rect(560, 180, 800, 620)
tradeButtons = [
    ("1개 사기",   1, pygame.Rect(600, 690, 170, 60)),
    ("10개 사기", 10, pygame.Rect(790, 690, 170, 60)),
    ("1개 팔기",  -1, pygame.Rect(980, 690, 170, 60)),
    ("10개 팔기", -10, pygame.Rect(1170, 690, 170, 60)),
]
def drawMap(camX, camY):
    """카메라 왼쪽 위 모서리(camX, camY)를 기준으로 보이는 타일만 그린다."""
    # 화면에 걸치는 타일 범위만 계산 (전체 90000칸을 다 그리지 않기 위해)
    startCol = camX // TILE
    endCol = (camX + screen_width) // TILE
    startRow = camY // TILE
    endRow = (camY + screen_height) // TILE

    for row in range(startRow, endRow + 1):
        if row < 0 or row >= sizeH:
            continue  # 맵 밖은 건너뛴다
        for col in range(startCol, endCol + 1):
            if col < 0 or col >= sizeW:
                continue

            # 월드 좌표 -> 화면 좌표
            x = col * TILE - camX
            y = row * TILE - camY

            rect = pygame.Rect(x, y, TILE, TILE)
            screen.blit(tile_grass, rect)
            #pygame.draw.rect(screen, tileColors.get(map[row][col], gray), rect)
            #pygame.draw.rect(screen, gridColor, rect, 1)  # 칸 구분선
def openinv():
    panel = pygame.Rect(460, 100, 1000, 200)
    pygame.draw.rect(screen, panelBg, panel)
    pygame.draw.rect(screen, panelLine, panel, 3)

    for i in range(10):
        rectInv = pygame.Rect(i * 95 + 490, 140, 80, 80)
        pygame.draw.rect(screen, slotBg, rectInv)
        pygame.draw.rect(screen, panelLine, rectInv, 2)

        slot = inv[i]
        if slot is not None:
            item = itemDefs[slot["id"]]
            pygame.draw.rect(screen, item["color"], rectInv.inflate(-16, -16))
            cnt = fontSmall.render(str(slot["count"]), True, black)
            screen.blit(cnt, (rectInv.right - cnt.get_width() - 4,
                              rectInv.bottom - cnt.get_height() - 2))

    screen.blit(font.render("벨: " + str(bells), True, black), (490, 245))


def drawMoo(camX, camY):
    """월드 좌표 rect를 카메라만큼 옮겨서 화면에 그린다"""
    r = Moo["rect"].move(-camX, -camY)   # move는 새 rect를 돌려줌 (원본 보존)
    pygame.draw.rect(screen, (245, 245, 250), r)
    pygame.draw.rect(screen, panelLine, r, 3)
    name = font.render(Moo["name"], True, white)
    screen.blit(name, (r.centerx - name.get_width() // 2, r.top - 34))


def nearMoo():
    """플레이어 중심이 Moo 주변 범위 안에 들어왔는가"""
    big = Moo["rect"].inflate(INTERACT_RANGE * 2, INTERACT_RANGE * 2)
    return big.collidepoint(playerX, playerY)


def buyMoo(n):
    global bells
    cost = mooNow * n
    # 벨을 빼기 전에 자리부터 확인 — 순서를 바꾸면 가방이 꽉 찼을 때 돈만 사라진다
    if bells >= cost and invSpace("moocoin", n):
        bells -= cost
        invAdd("moocoin", n)


def sellMoo(n):
    global bells
    if invRemove("moocoin", n):
        bells += mooNow * n


def drawTrade():
    pygame.draw.rect(screen, panelBg, tradePanel)
    pygame.draw.rect(screen, panelLine, tradePanel, 4)

    title = fontBig.render("무트코인 거래소", True, black)
    screen.blit(title, (tradePanel.centerx - title.get_width() // 2, tradePanel.top + 20))

    # 현재가 + 직전 슬롯 대비 변동
    diff = mooNow - mooPrev
    mark = "▲" if diff > 0 else ("▼" if diff < 0 else "-")
    markColor = upColor if diff > 0 else (downColor if diff < 0 else black)
    screen.blit(font.render("현재가", True, black), (tradePanel.left + 40, tradePanel.top + 88))
    price = fontBig.render(str(mooNow) + "벨", True, black)
    screen.blit(price, (tradePanel.left + 40, tradePanel.top + 118))
    screen.blit(font.render(mark + " " + str(abs(diff)), True, markColor),
                (tradePanel.left + 55 + price.get_width(), tradePanel.top + 128))

    # 다음 변동까지 남은 시간
    left = int(SLOT_SECONDS - (time.time() % SLOT_SECONDS))
    screen.blit(fontSmall.render("다음 변동까지 %d:%02d" % (left // 60, left % 60), True, black),
                (tradePanel.left + 40, tradePanel.top + 172))

    # 보유 현황
    screen.blit(font.render("보유 " + str(invCount("moocoin")) + "개", True, black),
                (tradePanel.right - 250, tradePanel.top + 96))
    screen.blit(font.render("벨 " + str(bells), True, black),
                (tradePanel.right - 250, tradePanel.top + 136))

    # 최근 2시간(5분 x 24칸) 가격 그래프
    graph = pygame.Rect(tradePanel.left + 40, tradePanel.top + 220, tradePanel.width - 80, 250)
    pygame.draw.rect(screen, white, graph)
    pygame.draw.rect(screen, panelLine, graph, 2)

    slot = currentSlot()
    hist = [mooPrice(slot - k) for k in range(23, -1, -1)]
    lo, hi = min(hist), max(hist)
    span = hi - lo if hi != lo else 1   # 0으로 나누기 방지

    points = []
    for i, p in enumerate(hist):
        gx = graph.left + 10 + i * (graph.width - 20) // (len(hist) - 1)
        gy = graph.bottom - 10 - (p - lo) * (graph.height - 20) // span
        points.append((gx, gy))
    pygame.draw.lines(screen, (200, 120, 40), False, points, 3)
    pygame.draw.circle(screen, upColor, points[-1], 6)   # 지금 위치

    screen.blit(fontSmall.render(str(hi), True, black), (graph.left + 6, graph.top + 4))
    screen.blit(fontSmall.render(str(lo), True, black), (graph.left + 6, graph.bottom - 26))
    screen.blit(fontSmall.render("최근 2시간", True, black), (graph.right - 100, graph.top + 4))

    for label, n, rect in tradeButtons:
        pygame.draw.rect(screen, btnBg, rect)
        pygame.draw.rect(screen, panelLine, rect, 2)
        t = font.render(label, True, black)
        screen.blit(t, (rect.centerx - t.get_width() // 2, rect.centery - t.get_height() // 2))

    screen.blit(fontSmall.render("ESC: 닫기", True, black),
                (tradePanel.left + 40, tradePanel.bottom - 32))


clock = pygame.time.Clock()

while running:
    dt = clock.tick(60) / 1000.0  # 60fps 고정 + 지난 시간(초)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            gameStarted = True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            inventoryOpened *= -1
        if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
            if gameStarted and nearMoo():
                tradeOpened *= -1
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            tradeOpened = -1
        if event.type == pygame.MOUSEBUTTONDOWN and tradeOpened > 0:
            for label, n, rect in tradeButtons:
                if rect.collidepoint(event.pos):
                    if n > 0:
                        buyMoo(n)
                    else:
                        sellMoo(-n)

    # 5분 슬롯이 바뀌었을 때만 시세를 다시 계산한다
    slotNow = currentSlot()
    if slotNow != mooSlot:
        mooSlot = slotNow
        mooNow = mooPrice(slotNow)
        mooPrev = mooPrice(slotNow - 1)

    # 이동 (방향키 / WASD) — 거래 중에는 못 움직인다
    if gameStarted and tradeOpened < 0:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            playerX -= playerSpeed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            playerX += playerSpeed * dt
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            playerY -= playerSpeed * dt
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            playerY += playerSpeed * dt
        # 맵 밖으로 못 나가게 (주인공 몸 크기만큼 여유를 둔다)
        playerX = max(playerW // 2, min(playerX, mapPixelW - playerW // 2))
        playerY = max(playerH // 2, min(playerY, mapPixelH - playerH // 2))

    screen.fill(white)  # 화면을 하얀색으로 채웁니다.
    if not gameStarted:
        screen.blit(startBg, ((1920-startBg.get_width())//2, (1080-startBg.get_height())//2-200))
    else:
        screen.fill((20, 20, 200))
        camX = int(playerX) - screen_width // 2
        camY = int(playerY) - screen_height // 2
        drawMap(camX, camY)
        drawMoo(camX, camY)

        # 주인공은 항상 화면 정중앙
        pygame.draw.rect(screen, blue, (screen_width // 2 - playerW // 2,
                                        screen_height // 2 - playerH // 2,
                                        playerW, playerH))

        # 가까이 가면 상호작용 안내
        if tradeOpened < 0 and nearMoo():
            tip = font.render("[F] " + Moo["name"] + "와 거래하기", True, white)
            r = Moo["rect"].move(-camX, -camY)
            screen.blit(tip, (r.centerx - tip.get_width() // 2, r.top - 72))

        # UI는 항상 맨 마지막에 (캐릭터가 창을 뚫고 나오지 않도록)
        if inventoryOpened > 0:
            openinv()
        if tradeOpened > 0:
            drawTrade()
    pygame.display.flip()  # 화면을 업데이트합니다.

# 4. 종료
pygame.quit()
