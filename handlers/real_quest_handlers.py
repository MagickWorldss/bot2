"""Real-life quest handlers."""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from services.real_quest_service import RealQuestService
from utils.keyboards import quests_menu_keyboard

logger = logging.getLogger(__name__)
router = Router()


class RealQuestStates(StatesGroup):
    """States for real quest."""
    waiting_for_code = State()


@router.callback_query(F.data == "real_quest_menu")
async def real_quest_menu(callback: CallbackQuery, user: User, session: AsyncSession):
    """Show real quest menu."""
    # Check if user has started quest
    progress = await RealQuestService.get_user_quest_progress(session, user.id)
    
    if not progress:
        # Quest not started
        await callback.message.edit_text(
            "🗺 **Квест поиска сокровищ**\n\n"
            "🎯 **Что это?**\n"
            "Это увлекательное приключение в реальной жизни!\n\n"
            "📍 **Как играть:**\n"
            "1. Зарегистрируйтесь в квесте\n"
            "2. Получите первое задание\n"
            "3. Найдите код в городе\n"
            "4. Введите код и получите следующее задание\n"
            "5. Пройдите все 20 заданий\n"
            "6. Получите уникальный физический приз!\n\n"
            "🎁 **Призы:**\n"
            "Каждый участник получает уникальный приз!\n"
            "После завершения квеста вы узнаете где его забрать.\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Готовы начать приключение?",
            reply_markup=_real_quest_start_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer()
        return
    
    # Quest in progress or completed
    if progress.is_completed:
        # Quest completed - show prize
        prize = await RealQuestService.get_prize_info(session, progress.prize_id)
        
        text = (
            "🗺 **Квест поиска сокровищ**\n\n"
            "🎉 **ПОЗДРАВЛЯЕМ!**\n\n"
            "Вы успешно завершили квест!\n\n"
            f"🎁 **Ваш приз:**\n"
            f"**{prize.prize_name}**\n\n"
            f"📝 **Описание:**\n{prize.prize_description}\n\n"
            f"📍 **Где забрать:**\n{prize.pickup_location}\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Спасибо за участие! 🎊"
        )
        
        if prize.prize_image_file_id:
            await callback.message.delete()
            await callback.message.answer_photo(
                photo=prize.prize_image_file_id,
                caption=text,
                reply_markup=quests_menu_keyboard(),
                parse_mode="Markdown"
            )
        else:
            await callback.message.edit_text(
                text,
                reply_markup=quests_menu_keyboard(),
                parse_mode="Markdown"
            )
        await callback.answer("🎉 Квест завершен!")
        return
    
    # Quest in progress - show current task
    task_info = await RealQuestService.get_current_task(session, user.id)
    
    if not task_info:
        await callback.message.edit_text(
            "❌ Ошибка загрузки задания.\n\n"
            "Обратитесь к администратору.",
            reply_markup=quests_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer("❌ Ошибка")
        return
    
    task_number = task_info['task_number']
    task_text = task_info['task_text_ru']
    hint = task_info.get('hint_ru')
    total = task_info['total_tasks']
    
    text = (
        f"🗺 **Квест поиска сокровищ**\n\n"
        f"📍 **Задание {task_number}/{total}**\n\n"
        f"{task_text}\n\n"
    )
    
    if hint:
        text += f"💡 **Подсказка:**\n{hint}\n\n"
    
    text += (
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🔍 Найдите код и введите его!"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=_real_quest_submit_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.callback_query(F.data == "real_quest_start")
async def real_quest_start(callback: CallbackQuery, user: User, session: AsyncSession):
    """Start real quest."""
    try:
        quest_progress = await RealQuestService.start_quest(session, user.id)
        
        # Show first task
        await real_quest_menu(callback, user, session)
        await callback.answer("✅ Квест начат!")
        
        logger.info(f"User {user.id} started real quest")
        
    except ValueError as e:
        await callback.message.edit_text(
            "😔 К сожалению, все призы уже разобраны.\n\n"
            "Следите за обновлениями!",
            reply_markup=quests_menu_keyboard(),
            parse_mode="Markdown"
        )
        await callback.answer("❌ Нет доступных призов")


@router.callback_query(F.data == "real_quest_submit_code")
async def real_quest_submit_code(callback: CallbackQuery, state: FSMContext):
    """Prompt for code submission."""
    await state.set_state(RealQuestStates.waiting_for_code)
    await callback.message.answer(
        "🔍 **Введите найденный код:**\n\n"
        "Код должен быть точным, без лишних пробелов."
    )
    await callback.answer()


@router.message(RealQuestStates.waiting_for_code)
async def real_quest_process_code(message: Message, user: User, session: AsyncSession, state: FSMContext):
    """Process submitted code."""
    code = message.text.strip()
    
    result = await RealQuestService.submit_code(session, user.id, code)
    
    if not result['success']:
        error_messages = {
            'quest_not_started': "❌ Вы не начали квест. Начните сначала!",
            'quest_already_completed': "✅ Вы уже завершили квест!",
            'task_not_found': "❌ Задание не найдено. Обратитесь к администратору.",
            'incorrect_code': "❌ Неверный код! Попробуйте еще раз."
        }
        error_msg = error_messages.get(result.get('error'), "❌ Ошибка")
        
        await message.answer(error_msg)
        
        if result.get('error') == 'incorrect_code':
            # Don't clear state, let user try again
            return
        else:
            await state.clear()
            return
    
    await state.clear()
    
    if result['completed']:
        # Quest completed!
        prize = await RealQuestService.get_prize_info(session, result['prize_id'])
        
        text = (
            "🎉 **ПОЗДРАВЛЯЕМ!**\n\n"
            "Вы завершили все 20 заданий!\n\n"
            f"🎁 **Ваш приз:**\n"
            f"**{prize.prize_name}**\n\n"
            f"📝 **Описание:**\n{prize.prize_description}\n\n"
            f"📍 **Где забрать:**\n{prize.pickup_location}\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "Спасибо за участие! 🎊"
        )
        
        if prize.prize_image_file_id:
            await message.answer_photo(
                photo=prize.prize_image_file_id,
                caption=text,
                parse_mode="Markdown"
            )
        else:
            await message.answer(text, parse_mode="Markdown")
        
        logger.info(f"User {user.id} completed real quest!")
        
    else:
        # Move to next task
        next_task = result['next_task']
        await message.answer(
            f"✅ **Правильно!**\n\n"
            f"Переходим к заданию {next_task}/20...\n\n"
            f"Используйте меню 'Квесты' → 'Квест поиска' для продолжения."
        )
        
        logger.info(f"User {user.id} completed task {next_task-1}")


def _real_quest_start_keyboard():
    """Start quest keyboard."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="🚀 Начать квест", callback_data="real_quest_start")
    builder.button(text="🔙 Назад", callback_data="quests_menu")
    builder.adjust(1)
    return builder.as_markup()


def _real_quest_submit_keyboard():
    """Submit code keyboard."""
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.button(text="📝 Ввести код", callback_data="real_quest_submit_code")
    builder.button(text="🔙 Назад", callback_data="quests_menu")
    builder.adjust(1)
    return builder.as_markup()

