"""Language and price list handlers."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, AdminLog
from services.user_service import UserService
from services.pricelist_service import pricelist_service
from services.language_service import language_service
from utils.language_keyboards import language_selection_keyboard, admin_pricelist_keyboard
from utils.keyboards import main_menu_keyboard, admin_menu_keyboard, cancel_keyboard
from utils.helpers import is_admin
from config import settings


router = Router(name='language_handlers')


class EditPriceListStates(StatesGroup):
    """States for editing price list."""
    waiting_for_content = State()


# Price List handlers
@router.message(F.text.in_(["💵 Прайс-лист", "💵 Price List", "💵 Kainų Sąrašas", "💵 Cennik", "💵 Preisliste", "💵 Ceník"]))
async def show_price_list(message: Message, user: User, session: AsyncSession):
    """Show price list."""
    price_list_text = await pricelist_service.get_price_list(session, user.language)
    await message.answer(price_list_text, parse_mode="Markdown")


# Language selection handlers
@router.message(F.text.in_(["🌐 Язык", "🌐 Language", "🌐 Kalba", "🌐 Język", "🌐 Sprache", "🌐 Jazyk"]))
async def select_language(message: Message, user: User):
    """Show language selection."""
    text = {
        'ru': '🌐 Выберите язык:',
        'en': '🌐 Select language:',
        'lt': '🌐 Pasirinkite kalbą:',
        'pl': '🌐 Wybierz język:',
        'de': '🌐 Sprache wählen:',
        'cs': '🌐 Vyberte jazyk:'
    }.get(user.language, '🌐 Выберите язык:')
    
    keyboard = language_selection_keyboard()
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("lang_"))
async def change_language(callback: CallbackQuery, user: User, session: AsyncSession):
    """Change user language."""
    new_language = callback.data.split("_")[1]
    
    # Update user language
    user.language = new_language
    await session.commit()
    
    # Get language name
    lang_name = language_service.get_language_name(new_language)
    
    success_messages = {
        'ru': f'✅ Язык изменен на: {lang_name}',
        'en': f'✅ Language changed to: {lang_name}',
        'lt': f'✅ Kalba pakeista į: {lang_name}',
        'pl': f'✅ Język zmieniony na: {lang_name}',
        'de': f'✅ Sprache geändert zu: {lang_name}',
        'cs': f'✅ Jazyk změněn na: {lang_name}'
    }
    
    await callback.message.edit_text(
        success_messages.get(new_language, success_messages['ru'])
    )
    
    # Send new menu with updated language
    keyboard = main_menu_keyboard(new_language)
    
    menu_messages = {
        'ru': '📱 Главное меню',
        'en': '📱 Main menu',
        'lt': '📱 Pagrindinis meniu',
        'pl': '📱 Menu główne',
        'de': '📱 Hauptmenü',
        'cs': '📱 Hlavní menu'
    }
    
    await callback.message.answer(
        menu_messages.get(new_language, menu_messages['ru']),
        reply_markup=keyboard
    )
    
    await callback.answer(f"✅ {lang_name}")


# Admin: Edit price list
@router.message(F.text == "✏️ Редактировать прайс-лист")
async def admin_edit_pricelist(message: Message, user: User):
    """Admin: edit price list."""
    if not is_admin(user.id, settings.admin_list):
        await message.answer("⛔️ У вас нет доступа к этой функции.")
        return
    
    keyboard = admin_pricelist_keyboard()
    
    await message.answer(
        "✏️ **Редактирование прайс-листа**\n\n"
        "Выберите язык для редактирования:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("edit_pricelist_"))
async def admin_edit_pricelist_lang(
    callback: CallbackQuery,
    state: FSMContext
):
    """Admin: select language to edit."""
    language = callback.data.split("_")[2]
    lang_name = language_service.get_language_name(language)
    
    await state.update_data(edit_pricelist_lang=language)
    await state.set_state(EditPriceListStates.waiting_for_content)
    
    await callback.message.answer(
        f"✏️ **Редактирование прайс-листа ({lang_name})**\n\n"
        f"Отправьте новый текст прайс-листа:\n\n"
        f"Можете использовать Markdown форматирование:\n"
        f"**жирный**, *курсив*, `код`\n\n"
        f"Или отправьте '-' чтобы сбросить на стандартный.",
        reply_markup=cancel_keyboard(),
        parse_mode="Markdown"
    )
    await callback.answer()


@router.message(EditPriceListStates.waiting_for_content)
async def admin_save_pricelist(
    message: Message,
    user: User,
    session: AsyncSession,
    state: FSMContext
):
    """Admin: save price list content."""
    if message.text == "❌ Отмена":
        await state.clear()
        await message.answer(
            "❌ Редактирование отменено.",
            reply_markup=admin_menu_keyboard()
        )
        return
    
    # Get language from state
    data = await state.get_data()
    language = data['edit_pricelist_lang']
    lang_name = language_service.get_language_name(language)
    
    # Get content
    if message.text == '-':
        # Reset to default
        content = pricelist_service._get_default_price_list(language)
    else:
        content = message.text
    
    # Save
    await pricelist_service.update_price_list(
        session,
        language,
        content,
        user.id
    )
    
    # Log
    log = AdminLog(
        admin_id=user.id,
        action="edit_pricelist",
        details=f"Edited price list for {language}"
    )
    session.add(log)
    await session.commit()
    
    await state.clear()
    
    await message.answer(
        f"✅ **Прайс-лист обновлен!**\n\n"
        f"Язык: {lang_name}\n\n"
        f"Предпросмотр:\n{content}",
        reply_markup=admin_menu_keyboard(),
        parse_mode="Markdown"
    )

