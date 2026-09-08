import pygame
import math
import random

# 1. 초기화
pygame.init()

# 2. 화면 설정
screen_width = 1920
screen_height = 1080
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("동물의숲비슷한거")

white = (255, 255, 255)
blue = (0, 0, 255)
black = (0, 0, 0)

# 폰트는 루프 밖에서 한 번만 만든다 (매 프레임 만들면 크게 느려짐)
font = pygame.font.SysFont("applesdgothicneo", 26)
fontBig = pygame.font.SysFont("applesdgothicneo", 40)
fontSmall = pygame.font.SysFont("applesdgothicneo", 20)

running = True
gameStarted = False

startBg = pygame.image.load("img/startingBg.png")
tile_grass = pygame.image.load("img/tile_1.jpeg")

map=[]
sizeW = 300 #타일가로개수
sizeH = 300 #타일세로개수
sizeTemp = []
tileX=0
tileY=0
#1:0도, 2:90도, 3:180도, 4:270도
direction = 1

# 맵 오른쪽에 바다를 만든다. 시작 지점(가로 150번 타일)에서 오른쪽으로 조금만 가면 바닷가
seaCol = 170      # 이 열부터 물
sandWidth = 4     # 물 앞의 모래사장 너비

for i in range(sizeH):
    # sin으로 해안선을 살짝 구불구불하게 (직선이면 너무 인공적으로 보인다)
    edge = seaCol + int(3 * math.sin(i * 0.15))
    for j in range(sizeW):
        if j >= edge:
            sizeTemp.append(0)              # 물
        elif j >= edge - sandWidth:
            sizeTemp.append(2)              # 모래
        else:
            sizeTemp.append(1)              # 잔디
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
playerPos = [playerX, playerY]
inv = []
invIndex = 0
#1 = 삽, 2 = 낚싯대, 10~19 = 물고기
for i in range(10):
    inv.append(0)
# 시험용 기본 지급 (루프 안에서 매 프레임 넣으면 물고기를 덮어써버린다)
inv[0] = 1
inv[1] = 2
print(inv)
inventoryOpened = -1 #1= True -1 = False

# --- 물고기 도감 -------------------------------------------------------------
# weight : 잘 걸리는 정도(클수록 흔함)
# base   : 타이밍을 아예 못 맞췄을 때의 기본 포획 확률
# zone   : 타이밍 바에서 초록 구간의 너비 비율 (작을수록 어렵다)
# speed  : 막대가 왕복하는 속도 (클수록 빠르다)
fishDefs = {
    10: {"name": "피라미",   "color": (190, 210, 220), "weight": 26, "base": 0.55, "zone": 0.34, "speed": 0.85, "price": 40},
    11: {"name": "붕어",     "color": (170, 160, 110), "weight": 22, "base": 0.50, "zone": 0.30, "speed": 0.95, "price": 70},
    12: {"name": "송사리",   "color": (230, 225, 170), "weight": 18, "base": 0.52, "zone": 0.30, "speed": 1.05, "price": 90},
    13: {"name": "잉어",     "color": (200, 130, 70),  "weight": 14, "base": 0.42, "zone": 0.26, "speed": 1.15, "price": 160},
    14: {"name": "농어",     "color": (120, 150, 130), "weight": 10, "base": 0.38, "zone": 0.24, "speed": 1.25, "price": 250},
    15: {"name": "참돔",     "color": (235, 120, 130), "weight": 7,  "base": 0.34, "zone": 0.21, "speed": 1.40, "price": 420},
    16: {"name": "가오리",   "color": (140, 120, 170), "weight": 5,  "base": 0.30, "zone": 0.19, "speed": 1.55, "price": 700},
    17: {"name": "참치",     "color": (60, 100, 160),  "weight": 3,  "base": 0.26, "zone": 0.16, "speed": 1.70, "price": 1200},
    18: {"name": "개복치",   "color": (150, 150, 155), "weight": 2,  "base": 0.22, "zone": 0.14, "speed": 1.85, "price": 2000},
    19: {"name": "산갈치",   "color": (240, 240, 250), "weight": 1,  "base": 0.18, "zone": 0.11, "speed": 2.10, "price": 5000},
}

# 인벤토리 칸에 그릴 색과 이름 (물고기가 아닌 도구도 같이)
itemColors = {1: (150, 110, 60), 2: (110, 70, 40)}
itemNames = {0: "빈칸", 1: "삽", 2: "낚싯대"}


def itemName(itemId):
    if itemId in fishDefs:
        return fishDefs[itemId]["name"]
    return itemNames.get(itemId, "?")


def itemColor(itemId):
    if itemId in fishDefs:
        return fishDefs[itemId]["color"]
    return itemColors.get(itemId, gray)


def addToInv(itemId):
    """빈칸(0) 중 가장 앞 번호에 넣는다. 자리가 없으면 -1"""
    for i in range(len(inv)):
        if inv[i] == 0:
            inv[i] = itemId
            return i
    return -1   # 가방이 꽉 찼을 때 처리는 아직 안 만듦


def pickFish():
    """weight를 확률로 써서 물고기 한 마리를 고른다"""
    total = 0
    for f in fishDefs.values():
        total += f["weight"]
    r = random.uniform(0, total)
    for fishId, f in fishDefs.items():
        r -= f["weight"]
        if r <= 0:
            return fishId
    return 10


# --- 낚시 상태 ---------------------------------------------------------------
# 0: 안 함 / 1: 던짐(입질 대기) / 2: 입질! / 3: 타이밍 바 / 4: 결과 표시
fishState = 0
fishTimer = 0.0        # 각 단계에서 남은(또는 지난) 시간
fishId = 0             # 지금 걸린 물고기 번호
barPos = 0.0           # 막대 위치 0.0 ~ 1.0
barDir = 1             # 1이면 오른쪽, -1이면 왼쪽
zoneCenter = 0.5       # 초록 구간의 중심
fishMsg = ""           # 결과 문구
fishMsgColor = white

barRect = pygame.Rect(screen_width // 2 - 320, 820, 640, 56)
BITE_WINDOW = 0.9      # 입질했을 때 F를 눌러야 하는 시간(초)


def facingTile():
    """바라보는 방향의 바로 앞 타일 좌표"""
    dx, dy = 0, 0
    if direction == 1:
        dy = -1
    elif direction == 2:
        dx = 1
    elif direction == 3:
        dy = 1
    elif direction == 4:
        dx = -1
    return tileX + dx, tileY + dy


def tileAt(col, row):
    if col < 0 or col >= sizeW or row < 0 or row >= sizeH:
        return -1
    return map[row][col]


def holdingRod():
    return inv[invIndex] == 2


def canFish():
    """낚싯대를 들고, 바라보는 앞이 물이면 낚시 가능"""
    if not holdingRod():
        return False
    col, row = facingTile()
    return tileAt(col, row) == 0


def startFishing():
    global fishState, fishTimer, fishId, fishMsg
    fishState = 1
    fishTimer = random.uniform(1.2, 4.0)   # 입질까지 기다리는 시간
    fishId = 0
    fishMsg = ""


def stopFishing():
    global fishState, fishMsg
    fishState = 0
    fishMsg = ""


def startBar():
    """입질에 성공 -> 타이밍 바 시작"""
    global fishState, barPos, barDir, zoneCenter
    fishState = 3
    barPos = 0.0
    barDir = 1
    # 초록 구간이 화면 밖으로 나가지 않게 가장자리를 피해서 중심을 잡는다
    half = fishDefs[fishId]["zone"] / 2
    zoneCenter = random.uniform(half + 0.05, 1 - half - 0.05)


def judgeBar():
    """지금 막대 위치로 포획 성공 여부를 판정한다"""
    global fishState, fishTimer, fishMsg, fishMsgColor
    f = fishDefs[fishId]
    half = f["zone"] / 2
    dist = abs(barPos - zoneCenter)

    if dist <= half:
        acc = 1 - dist / half              # 중앙에 가까울수록 1에 가깝다
        chance = f["base"] + 0.45 * acc    # 타이밍이 좋을수록 확률이 올라간다
        if chance > 0.98:
            chance = 0.98
    else:
        acc = 0
        chance = f["base"] * 0.25          # 빗나가면 확률이 크게 깎인다

    if random.random() < chance:
        slot = addToInv(fishId)
        if acc > 0.9:
            fishMsg = "완벽! " + f["name"] + "를(을) 잡았다!  (" + str(slot + 1) + "번 칸)"
        else:
            fishMsg = f["name"] + "를(을) 잡았다!  (" + str(slot + 1) + "번 칸)"
        fishMsgColor = (255, 240, 140)
    else:
        fishMsg = f["name"] + "를(을) 놓쳤다..."
        fishMsgColor = (255, 170, 170)

    fishState = 4
    fishTimer = 2.0


def updateFishing(dt):
    global fishState, fishTimer, fishId, barPos, barDir, fishMsg, fishMsgColor

    if fishState == 1:                     # 입질 대기
        fishTimer -= dt
        if fishTimer <= 0:
            fishId = pickFish()
            fishState = 2
            fishTimer = BITE_WINDOW

    elif fishState == 2:                   # 입질! F를 눌러야 한다
        fishTimer -= dt
        if fishTimer <= 0:
            fishMsg = "너무 늦었다... 물고기가 도망갔다"
            fishMsgColor = (255, 170, 170)
            fishState = 4
            fishTimer = 1.6

    elif fishState == 3:                   # 막대 왕복
        barPos += fishDefs[fishId]["speed"] * barDir * dt
        if barPos >= 1.0:
            barPos = 1.0
            barDir = -1
        elif barPos <= 0.0:
            barPos = 0.0
            barDir = 1

    elif fishState == 4:                   # 결과 문구 보여주는 중
        fishTimer -= dt
        if fishTimer <= 0:
            fishState = 0
            fishMsg = ""


def fishKey():
    """낚시 중 F를 눌렀을 때"""
    if fishState == 0:
        if canFish():
            startFishing()
    elif fishState == 1:
        stopFishing()                      # 아직 입질 전이면 그만두기
    elif fishState == 2:
        startBar()                         # 제때 챘다
    elif fishState == 3:
        judgeBar()


def drawRod():
    """낚싯대와 찌를 rect로 (그림은 나중에 교체)"""
    px = screen_width // 2
    py = screen_height // 2

    dx, dy = 0, 0
    if direction == 1:
        dy = -1
    elif direction == 2:
        dx = 1
    elif direction == 3:
        dy = 1
    elif direction == 4:
        dx = -1

    # 손에 든 낚싯대 (방향에 따라 눕혔다 세웠다)
    if dx != 0:
        rod = pygame.Rect(px + dx * 24 - (0 if dx > 0 else 60), py - 6, 60, 8)
    else:
        rod = pygame.Rect(px - 4, py + dy * 24 - (0 if dy > 0 else 60), 8, 60)
    pygame.draw.rect(screen, (110, 70, 40), rod)

    if fishState == 0:
        return

    # 찌: 바라보는 방향으로 조금 떨어진 물 위
    bx = px + dx * 190
    by = py + dy * 190
    if fishState == 2:
        # 입질 중에는 찌가 잘게 흔들린다
        bx += random.randint(-4, 4)
        by += random.randint(-4, 4)

    pygame.draw.line(screen, white, rod.center, (bx, by), 2)
    bob = pygame.Rect(bx - 9, by - 9, 18, 18)
    pygame.draw.rect(screen, (230, 70, 70) if fishState == 2 else white, bob)
    pygame.draw.rect(screen, black, bob, 2)

    if fishState == 2:
        mark = fontBig.render("!", True, (255, 80, 80))
        screen.blit(mark, (bx - mark.get_width() // 2, by - 60))


def drawFishUI():
    if fishState == 1:
        tip = font.render("입질을 기다리는 중...  [F] 그만두기", True, white)
        screen.blit(tip, (screen_width // 2 - tip.get_width() // 2, 780))

    elif fishState == 2:
        tip = fontBig.render("지금이야!  [F]", True, (255, 230, 120))
        screen.blit(tip, (screen_width // 2 - tip.get_width() // 2, 760))

    elif fishState == 3:
        f = fishDefs[fishId]
        # 바 배경
        pygame.draw.rect(screen, (40, 40, 50), barRect)
        pygame.draw.rect(screen, white, barRect, 3)

        # 초록 구간 (여기서 멈출수록 포획 확률이 올라간다)
        half = f["zone"] / 2
        zx = barRect.left + int((zoneCenter - half) * barRect.width)
        zw = int(f["zone"] * barRect.width)
        pygame.draw.rect(screen, (80, 200, 110), (zx, barRect.top + 4, zw, barRect.height - 8))
        # 한가운데(가장 확률이 높은 곳)
        cx = barRect.left + int(zoneCenter * barRect.width)
        pygame.draw.rect(screen, (255, 240, 150), (cx - 3, barRect.top + 4, 6, barRect.height - 8))

        # 움직이는 막대
        mx = barRect.left + int(barPos * barRect.width)
        pygame.draw.rect(screen, (250, 90, 90), (mx - 5, barRect.top - 8, 10, barRect.height + 16))

        tip = font.render("[F] 초록 칸 한가운데에서 멈추기!", True, white)
        screen.blit(tip, (screen_width // 2 - tip.get_width() // 2, barRect.top - 50))

    elif fishState == 4:
        msg = fontBig.render(fishMsg, True, fishMsgColor)
        screen.blit(msg, (screen_width // 2 - msg.get_width() // 2, 790))


#npc는 rect, 위치로 저장
def drawMap(posX, posY):
    """주인공(posX, posY)을 화면 중앙에 두고, 보이는 타일만 그린다."""
    # 카메라 왼쪽 위 모서리의 월드 좌표
    camX = posX - screen_width // 2
    camY = posY - screen_height // 2

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
            if map[row][col] == 1:
                screen.blit(tile_grass, rect)
            else:
                pygame.draw.rect(screen, tileColors.get(map[row][col], gray), rect)
            #pygame.draw.rect(screen, gridColor, rect, 1)  # 칸 구분선
def openinv():
    rect = pygame.Rect(460, 100, 1000, 200)
    pygame.draw.rect(screen, white, rect)
    for i in range(10):
        rectInv = pygame.Rect(i * 100 + 490, 130, 40, 40)
        # 지금 고른 칸은 테두리로 표시
        pygame.draw.rect(screen, itemColor(inv[i]) if inv[i] != 0 else blue, rectInv)
        if i == invIndex:
            pygame.draw.rect(screen, (230, 60, 60), rectInv.inflate(8, 8), 3)
        if inv[i] != 0:
            nm = fontSmall.render(itemName(inv[i]), True, black)
            screen.blit(nm, (rectInv.centerx - nm.get_width() // 2, rectInv.bottom + 4))
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
            if gameStarted:
                fishKey()
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if fishState != 0:
                stopFishing()
        # 마우스 처리도 이 루프 안에서 해야 한다 (event.get()을 또 부르면 이벤트를 빼앗김)
        if event.type == pygame.MOUSEBUTTONDOWN and inventoryOpened > 0:
            #인벤토리에서 선택한 칸 번호 찾기
            if event.pos[1] >= 130 and event.pos[1] <= 170:
                for i in range(10):
                    if (490 + 100*i) < event.pos[0] and (530 + 100*i) > event.pos[0]:
                        invIndex = i



    # 이동 (방향키 / WASD) — 낚시 중에는 못 움직인다
    if gameStarted and fishState == 0:
        keys = pygame.key.get_pressed()
        newX = playerX
        newY = playerY
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            newX -= playerSpeed * dt
            direction = 4
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            newX += playerSpeed * dt
            direction = 2
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            newY -= playerSpeed * dt
            direction = 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            newY += playerSpeed * dt
            direction = 3

        # 물 타일 위로는 걸어 들어가지 않는다 (x, y를 따로 검사해야 벽을 스치듯 지나갈 수 있다)
        if tileAt(int(newX) // TILE, int(playerY) // TILE) != 0:
            playerX = newX
        if tileAt(int(playerX) // TILE, int(newY) // TILE) != 0:
            playerY = newY

        # 맵 밖으로 못 나가게 (주인공 몸 크기만큼 여유를 둔다)
        playerX = max(playerW // 2, min(playerX, mapPixelW - playerW // 2))
        playerY = max(playerH // 2, min(playerY, mapPixelH - playerH // 2))

        # 월드 좌표(픽셀) -> 타일 좌표. map[tileY][tileX] 로 바로 쓸 수 있다
        tileX = int(playerX) // TILE
        tileY = int(playerY) // TILE
        # 인덱스 범위 밖으로는 절대 나가지 않게 (map[tileY][tileX] 안전 보장)
        tileX = max(0, min(tileX, sizeW - 1))
        tileY = max(0, min(tileY, sizeH - 1))

    if gameStarted:
        updateFishing(dt)

    screen.fill(white)  # 화면을 하얀색으로 채웁니다.
    if not gameStarted:
        screen.blit(startBg, ((1920-startBg.get_width())//2, (1080-startBg.get_height())//2-200))
    else:
        screen.fill((20, 20, 200))
        drawMap(int(playerX), int(playerY))

        # 주인공은 항상 화면 정중앙
        pygame.draw.rect(screen, blue, (screen_width // 2 - playerW // 2,
                                        screen_height // 2 - playerH // 2,
                                        playerW, playerH))
        # 낚싯대를 든 상태면 손에 그린다
        if holdingRod():
            drawRod()

        # 물가에서 낚싯대를 들고 있으면 안내
        if fishState == 0 and canFish():
            tip = font.render("[F] 낚시하기", True, white)
            screen.blit(tip, (screen_width // 2 - tip.get_width() // 2, screen_height // 2 - 80))

        drawFishUI()

        # UI는 항상 맨 마지막에 (캐릭터가 창을 뚫고 나오지 않도록)
        if inventoryOpened > 0:
            openinv()

        info = f"플레이어 위치 타일 : {tileX}, {tileY}  (타일값 {map[tileY][tileX]}), 도구값 : {inv[invIndex]} ({itemName(inv[invIndex])})"
        screen.blit(font.render(info, True, black), (30, 30))
    pygame.display.flip()  # 화면을 업데이트합니다.

# 4. 종료
pygame.quit()
