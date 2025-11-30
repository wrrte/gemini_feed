import datetime
import os

from PIL import Image, ImageDraw, ImageFont

from database.schema.camera import CameraSchema


class SafeHomeCamera:
    MAX_ZOOM = 5
    MIN_ZOOM = 1
    MAX_PAN = 3
    MIN_PAN = -3
    RETURN_SIZE = 500

    def __init__(
        self,
        camera_id: int = 0,
        coordinate_x: int = 0,
        coordinate_y: int = 0,
        pan: int = 0,
        zoom_setting: int = 1,
        has_password: bool = False,
        password: str | None = None,
        enabled: bool = False,
        **kwargs,  # created_at, updated_at 등 추가 필드 무시
    ):
        self.camera_id = camera_id
        self.location = (coordinate_x, coordinate_y)
        self.pan = pan
        self.zoom_setting = zoom_setting
        self._has_password = has_password
        self._locked = has_password  # 비밀번호가 있으면 잠금 상태
        self.password = password
        self.enabled = enabled
        self.image = None

        self.font = ImageFont.load_default()

        # camera_id가 설정되어 있으면 이미지 로드
        if self.camera_id > 0:
            self._load_img()

    def _load_img(self) -> None:
        print(f"[Camera {self.camera_id}] Loading image..")

        current_dir = os.path.dirname(os.path.abspath(__file__))
        img_dir = os.path.abspath(os.path.join(current_dir, "../../img"))

        if self.camera_id in [1, 2, 3]:
            image_path = img_dir + f"/camera{self.camera_id}.jpg"
        else:
            image_path = img_dir + "/camera_default.jpg"

        try:
            self.image = Image.open(image_path)
            print(f"[Camera {self.camera_id}] Done loading image")
        except FileNotFoundError:
            print(
                f"[Camera {self.camera_id}] Error: File {image_path} \
                 does not exists"
            )
            self.image = None

    def get_location(self) -> tuple[int, int]:
        return self.location

    def set_location(self, location: tuple[int, int]) -> bool:
        is_changed = self.location != location
        self.location = location
        return is_changed

    def get_id(self) -> int:
        return self.camera_id

    def set_id(self, camera_id: int) -> bool:
        is_changed = self.camera_id != camera_id
        self.camera_id = camera_id
        self._load_img()

        return is_changed

    def display_view(self) -> Image.Image:
        assert (
            self.zoom_setting <= self.MAX_ZOOM
            and self.MIN_ZOOM <= self.zoom_setting
        )
        assert self.MIN_PAN <= self.pan and self.pan <= self.MAX_PAN

        if self.image is None:
            self._load_img()

        img_view = Image.new(
            "RGB", (self.RETURN_SIZE, self.RETURN_SIZE), "black"
        )

        if self.enabled is False or self._locked is True:
            return img_view

        width, height = self.image.size
        source_size = min(width, height)
        center_x, center_y = width / 2, height / 2
        zoomed = source_size * 0.35 * (1 - self.zoom_setting / 10)
        panned = self.pan * source_size / 20

        left = center_x + panned - zoomed
        upper = center_y - zoomed
        right = center_x + panned + zoomed
        lower = center_y + zoomed

        cropped = self.image.crop([left, upper, right, lower])
        resized = cropped.resize([self.RETURN_SIZE, self.RETURN_SIZE])
        img_view.paste(resized, (0, 0))

        draw = ImageDraw.Draw(img_view)

        now = datetime.datetime.now()
        formatted = now.strftime("%Y-%m-%d %H:%M:%S")
        view = f"time: {formatted}, "

        view += f"zoom x{self.zoom_setting}, "

        if self.pan > 0:
            view += f"right {self.pan}"
        elif self.pan == 0:
            view += "center"
        else:
            view += f"left {-self.pan}"

        # Get text size
        bbox = draw.textbbox((0, 0), view, font=self.font)
        w_text = bbox[2] - bbox[0]
        h_text = bbox[3] - bbox[1]

        # Draw rounded rectangle background (gray)
        r_x = 0
        r_y = 0
        draw.rounded_rectangle(
            [(r_x, r_y), (r_x + w_text + 10, r_y + h_text + 5)],
            radius=h_text // 2,
            fill="gray",
        )

        # Draw text (cyan)
        x_text = r_x + 5
        y_text = r_y + 2
        draw.text((x_text, y_text), view, fill="white", font=self.font)

        return img_view

    def pan_right(self) -> bool:
        if self.pan >= self.MAX_PAN:
            self.pan = self.MAX_PAN
            return False

        self.pan += 1
        return True

    def pan_left(self) -> bool:
        if self.pan <= self.MIN_PAN:
            self.pan = self.MIN_PAN
            return False

        self.pan -= 1
        return True

    def zoom_in(self) -> bool:
        if self.zoom_setting >= self.MAX_ZOOM:
            self.zoom_setting = self.MAX_ZOOM
            return False

        self.zoom_setting += 1
        return True

    def zoom_out(self) -> bool:
        if self.zoom_setting <= self.MIN_ZOOM:
            self.zoom_setting = self.MIN_ZOOM
            return False

        self.zoom_setting -= 1
        return True

    def has_password(self) -> bool:
        return self._has_password

    def get_password(self) -> str:
        return self.password

    def set_password(self, new_password: str | None) -> bool:
        """
        Sets a new password for the camera.
        If new_password is None, removes the existing password
        and unlocks the camera.
        If a new password is provided, sets it and locks the camera.
        """
        # If new_password is None, removes the existing password
        if new_password is None:
            self.password = None
            self._has_password = False
            self.unlock()
            return False

        self.password = new_password
        self._has_password = True
        self.lock()
        return True

    def is_locked(self) -> bool:
        return self._locked

    def lock(self) -> None:
        self._locked = True

    def unlock(self) -> None:
        self._locked = False

    def is_enabled(self) -> bool:
        return self.enabled

    def enable(self) -> None:
        self.enabled = True

    def disable(self) -> None:
        self.enabled = False

    def to_schema(self) -> CameraSchema:
        return CameraSchema(
            camera_id=self.camera_id,
            coordinate_x=self.location[0],
            coordinate_y=self.location[1],
            pan=self.pan,
            zoom_setting=self.zoom_setting,
            has_password=self._has_password,
            password=self.password,
            enabled=self.enabled,
        )

    def get_info(self) -> dict:
        dump = self.to_schema().model_dump()
        dump["locked"] = self._locked
        return dump
