from services.db_context import db
from typing import Optional, Union, List
from datetime import datetime, timedelta
import random
import pytz


class Genshin(db.Model):
    __tablename__ = "test"

    user_id = db.Column(db.String(), primary_key=True)
    uid = db.Column(db.String())
    last_time = db.Column(db.String())

    _idx1 = db.Index("test_idx1", "user_id", "uid", unique=True)


    @classmethod
    async def update_last_query(cls, user_id: str, uid: str) -> bool:
        """
        说明:
            设置更新uid
        参数:
            :param user_id: 用户QQ号
            :param uid: 原神id
            :param last_time: 更新时间
        """
        query = cls.query.where(cls.user_id == user_id).with_for_update()
        user = await query.gino.first()
        t = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if user:
            await user.update(uid=uid).apply()
            await user.update(last_time=t).apply()
        else:
            await cls.create(
                user_id=user_id,
                uid=uid,
                last_time=t,
            )


    @classmethod
    async def get_last_query(cls, user_id: str) -> Optional[str]:
        """
        说明:
            获取用户uid
        参数:
            :param user_id: 用户QQ号
            :param uid: 原神id
            :param last_time: 更新时间
        """
        user = await cls.query.where(cls.user_id == user_id).gino.first()
        if user:
            return user.uid 
        return None