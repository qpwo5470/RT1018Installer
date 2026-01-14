#!/usr/bin/env python3
"""
Apply Korean translations to rt1018_installer_gui.py
"""

def apply_translations():
    file_path = r'C:\Users\qpwo5\PycharmProjects\RT1018Installer\rt1018_installer_gui.py'

    # Read file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # All translation pairs (English -> Korean)
    translations = [
        # Installation messages
        ('"Installing to device ', '"디바이스에 설치 중 '),
        ('"[1/10] Requesting root access..."', '"[1/10] 루트 권한 요청 중..."'),
        ('"Waiting for device restart..."', '"디바이스 재시작 대기 중..."'),
        ('"Device ready after ', '"디바이스 준비 완료: '),
        ('"[2/10] Installing APK files..."', '"[2/10] APK 파일 설치 중..."'),
        ('"Installing ', '"설치 중: '),
        ('"APK not found: ', '"APK를 찾을 수 없음: '),
        ('"[3/10] Granting app permissions..."', '"[3/10] 앱 권한 부여 중..."'),
        ('"[4/10] Launching app to initialize..."', '"[4/10] 앱 초기화 시작..."'),
        ('"Starting scrcpy to monitor installation..."', '"설치 모니터링을 위해 scrcpy 시작..."'),
        ('"[5/10] Transferring files..."', '"[5/10] 파일 전송 중..."'),
        ('"Pushing files to /sdcard..."', '"/sdcard로 파일 전송 중..."'),
        ('"File transfer timed out (>5 minutes). Check network connection."', '"파일 전송 시간 초과 (5분 초과). 네트워크 연결을 확인하세요."'),
        ('"Remounting system..."', '"시스템 재마운트 중..."'),
        ('"Pushing app files to /data/data..."', '"/data/data로 앱 파일 전송 중..."'),
        ('"Pushing database..."', '"데이터베이스 전송 중..."'),
        ('"Pushing preferences..."', '"환경설정 전송 중..."'),
        ('"[6/10] Fixing file ownership..."', '"[6/10] 파일 소유권 수정 중..."'),
        ('"Android 12+ detected, applying chown..."', '"Android 12+ 감지됨, chown 적용 중..."'),
        ('"Setting ownership to ', '"소유권 설정 중: '),
        ('"[7/10] Stopping app..."', '"[7/10] 앱 중지 중..."'),
        ('"[8/10] Setting system language and keyboard..."', '"[8/10] 시스템 언어 및 키보드 설정 중..."'),
        ('"[9/10] Rebooting device..."', '"[9/10] 디바이스 재부팅 중..."'),
        ('"Waiting for device to reboot..."', '"디바이스 재부팅 대기 중..."'),
        ('"Waiting for device to come back online..."', '"디바이스 온라인 대기 중..."'),
        ('"Device back online after ', '"디바이스 온라인 복귀: '),
        ('" seconds"', '"초"'),
        ('"Device taking longer than expected to reboot, continuing anyway..."', '"디바이스 재부팅이 예상보다 오래 걸림, 그래도 계속 진행..."'),
        ('"[10/10] Setting home app..."', '"[10/10] 홈 앱 설정 중..."'),
        ('"✅ Installation completed for ', '"✅ 설치 완료: '),
        ('"✅ Installation completed successfully for ', '"✅ 설치 성공: '),
        ('"❌ Installation failed for ', '"❌ 설치 실패: '),
        ('"\\n🎉 All installations completed!"', '"\\n🎉 모든 설치 완료!"'),
        ('"Scrcpy is still running for the last device - click ', '"Scrcpy가 마지막 디바이스에서 계속 실행 중 - '),
        ("\"'Stop Scrcpy' when done\"", '"완료되면 \'Scrcpy 중지\'를 클릭하세요"'),
        ('"Installation complete"', '"설치 완료"'),

        # Error messages
        ('"No devices selected"', '"선택된 디바이스 없음"'),
        ('"Please select at least one device to install to."', '"최소 1개 이상의 디바이스를 선택해주세요."'),
        ('"No backup selected"', '"선택된 백업 없음"'),
        ('"Please select a backup to install from."', '"설치할 백업을 선택해주세요."'),

        # Scrcpy messages
        ('"→ Scrcpy auto-started for ', '"→ Scrcpy 자동 시작: '),
        ('"✓ Scrcpy embedded successfully!"', '"✓ Scrcpy 임베드 성공!"'),
        ('"Scrcpy disconnected (device rebooting or disconnected)"', '"Scrcpy 연결 끊김 (디바이스 재부팅 또는 연결 끊김)"'),
        ('"Scrcpy stopped (exit code: ', '"Scrcpy 중지됨 (종료 코드: '),
        ('"Stopping scrcpy..."', '"Scrcpy 중지 중..."'),
        ('"Scrcpy stopped"', '"Scrcpy 중지됨"'),
        ('"Cannot embed scrcpy: pywin32 not installed"', '"Scrcpy 임베드 불가: pywin32 미설치"'),
        ('"Scrcpy not available - continuing without screen view"', '"Scrcpy 사용 불가 - 화면 보기 없이 계속"'),
        ('"Could not start scrcpy: ', '"Scrcpy 시작 실패: '),
        ('"Scrcpy failed\\n\\nInstalling..."', '"Scrcpy 실패\\n\\n설치 중..."'),
        ('"Starting scrcpy for\\n', '"Scrcpy 시작 중: \\n'),
        ('"...\\nPlease wait..."', '"...\\n잠시 기다려주세요..."'),
        ('"Scrcpy not available\\n\\nInstalling..."', '"Scrcpy 사용 불가\\n\\n설치 중..."'),

        # Backup messages
        ('"Backup from Device"', '"디바이스에서 백업"'),
        ('"Please select exactly one device for backup."', '"백업할 디바이스를 정확히 1개 선택해주세요."'),
        ('"Starting backup from ', '"백업 시작: '),
        ('"Backup location: ', '"백업 위치: '),
        ('"Creating backup directory..."', '"백업 디렉토리 생성 중..."'),
        ('"Backing up APK..."', '"APK 백업 중..."'),
        ('"Backing up files from /sdcard..."', '"/sdcard에서 파일 백업 중..."'),
        ('"Sdcard backup: ', '"SD카드 백업: '),
        ('"Backing up app files from /data/data..."', '"/data/data에서 앱 파일 백업 중..."'),
        ('"App files backup: ', '"앱 파일 백업: '),
        ('"Backing up database..."', '"데이터베이스 백업 중..."'),
        ('"Database backup: ', '"데이터베이스 백업: '),
        ('"Backing up preferences..."', '"환경설정 백업 중..."'),
        ('"Preferences backup: ', '"환경설정 백업: '),
        ('"\\n✅ Backup completed successfully!"', '"\\n✅ 백업 완료!"'),
        ('"Backup saved to: ', '"백업 저장 위치: '),
        ('"❌ Backup failed: ', '"❌ 백업 실패: '),

        # Database cleanup messages
        ('"Select MainDatabase.db"', '"MainDatabase.db 선택"'),
        ('"Database files"', '"데이터베이스 파일"'),
        ('"All files"', '"모든 파일"'),
        ('"Starting database image cleanup"', '"데이터베이스 이미지 정리 시작"'),
        ('"Database: ', '"데이터베이스: '),
        ('"Image directory: ', '"이미지 디렉토리: '),
        ('"Step 1: Removing non-hex hash files..."', '"단계 1: 비-헥스 해시 파일 제거 중..."'),
        ('"Found ', '"발견: '),
        ('" non-hex hash files to remove"', '"개의 비-헥스 해시 파일 제거 예정"'),
        ('"Removed non-hex file: ', '"비-헥스 파일 제거됨: '),
        ('"✓ Moved ', '"✓ 이동 완료: '),
        ('" non-hex files to ', '"개의 비-헥스 파일 -> '),
        ('"✓ All files are in hex hash format\\n"', '"✓ 모든 파일이 헥스 해시 형식\\n"'),
        ('"Step 2: Scanning database for image references..."', '"단계 2: 데이터베이스에서 이미지 참조 스캔 중..."'),
        ('"Error reading table ', '"테이블 읽기 오류: '),
        ('"\\n✓ Total unique image hashes in database: ', '"\\n✓ 데이터베이스의 총 고유 이미지 해시: '),
        ('"Step 3: Finding orphaned image files..."', '"단계 3: 고아 이미지 파일 찾기..."'),
        ('" orphaned files out of ', '"개의 고아 파일 발견 (전체 '),
        ('" hex files"', '"개의 헥스 파일 중)"'),
        ('"\\nExamples of orphaned files:"', '"\\n고아 파일 예시:"'),
        ('"  ... and ', '"  ... 외 '),
        ('" more"', '"개 추가"'),
        ('"Confirm Deletion"', '"삭제 확인"'),
        ('"Found.*orphaned files.', '"발견: '),
        ('"These files are not referenced in the database."', '"이 파일들은 데이터베이스에서 참조되지 않습니다."'),
        ('"Move them to', '"다음 폴더로 이동하시겠습니까'),
        ('"Moved: ', '"이동됨: '),
        ('"\\n✅ Cleanup completed! Moved ', '"\\n✅ 정리 완료! 이동됨: '),
        ('" files to ', '"개 파일 -> '),
        ('"Cleanup completed!', '"정리 완료!'),
        ('"- Removed ', '"- 제거됨: '),
        ('"- Moved ', '"- 이동됨: '),
        ('"Cleanup cancelled by user"', '"사용자가 정리 취소"'),
        ('"✓ No orphaned files found!"', '"✓ 고아 파일 없음!"'),
        ('"No orphaned files found!"', '"고아 파일 없음!"'),
        ('"Cleanup Complete"', '"정리 완료"'),
        ('"❌ Cleanup failed: ', '"❌ 정리 실패: '),
        ('"Cleanup Error"', '"정리 오류"'),
        ('"Failed to cleanup: ', '"정리 실패: '),

        # Status updates
        ('text="Connected"', 'text="연결됨"'),
    ]

    # Apply all translations
    for old, new in translations:
        content = content.replace(old, new)

    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✅ Applied {len(translations)} translations")
    print("File updated: rt1018_installer_gui.py")

if __name__ == '__main__':
    apply_translations()
