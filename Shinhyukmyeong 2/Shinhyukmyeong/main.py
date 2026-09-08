import pygame

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
playerPos = [playerX, playerY]
inv = []
invIndex = 0
#1 = 삽
for i in range(10):
    inv.append(0)
print(inv)
inventoryOpened = -1 #1= True -1 = False

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
            screen.blit(tile_grass, rect)
            #pygame.draw.rect(screen, tileColors.get(map[row][col], gray), rect)
            #pygame.draw.rect(screen, gridColor, rect, 1)  # 칸 구분선
def openinv():
    rect = pygame.Rect(460, 100, 1000, 200)
    pygame.draw.rect(screen, white, rect)
    for i in range(10):
        rectInv = pygame.Rect(i * 100 + 490, 130, 40, 40)
        pygame.draw.rect(screen, blue, rectInv)
clock = pygame.time.Clock()

while running:

    dt = clock.tick(60) / 1000.0  # 60fps 고정 + 지난 시간(초)
    inv[0] = 1

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            gameStarted = True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            inventoryOpened *= -1
        # 마우스 처리도 이 루프 안에서 해야 한다 (event.get()을 또 부르면 이벤트를 빼앗김)
        if event.type == pygame.MOUSEBUTTONDOWN and inventoryOpened > 0:
            #인벤토리에서 선택한 칸 번호 찾기
            if event.pos[1] >= 130 and event.pos[1] <= 170:
                for i in range(10):
                    if (490 + 100*i) < event.pos[0] and (530 + 100*i) > event.pos[0]:
                        invIndex = i



    # 이동 (방향키 / WASD)
    if gameStarted:
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            playerX -= playerSpeed * dt
            direction = 4
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            playerX += playerSpeed * dt
            direction = 2
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            playerY -= playerSpeed * dt
            direction = 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            playerY += playerSpeed * dt
            direction = 3
        # 맵 밖으로 못 나가게 (주인공 몸 크기만큼 여유를 둔다)
        playerX = max(playerW // 2, min(playerX, mapPixelW - playerW // 2))
        playerY = max(playerH // 2, min(playerY, mapPixelH - playerH // 2))

        # 월드 좌표(픽셀) -> 타일 좌표. map[tileY][tileX] 로 바로 쓸 수 있다
        tileX = int(playerX) // TILE
        tileY = int(playerY) // TILE
        # 인덱스 범위 밖으로는 절대 나가지 않게 (map[tileY][tileX] 안전 보장)
        tileX = max(0, min(tileX, sizeW - 1))
        tileY = max(0, min(tileY, sizeH - 1))

    screen.fill(white)  # 화면을 하얀색으로 채웁니다.
    if not gameStarted:
        screen.blit(startBg, ((1920-startBg.get_width())//2, (1080-startBg.get_height())//2-200))
    else:
        screen.fill((20, 20, 200))
        drawMap(int(playerX), int(playerY))

        if inventoryOpened > 0:
            openinv()
        # 주인공은 항상 화면 정중앙
        pygame.draw.rect(screen, blue, (screen_width // 2 - playerW // 2,
                                        screen_height // 2 - playerH // 2,
                                        playerW, playerH))

        info = f"플레이어 위치 타일 : {tileX}, {tileY}  (타일값 {map[tileY][tileX]}), 도구값 : {inv[invIndex]}"
        screen.blit(font.render(info, True, black), (30, 30))
    pygame.display.flip()  # 화면을 업데이트합니다.

# 4. 종료
pygame.quit()