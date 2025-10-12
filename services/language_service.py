"""Language service for multi-language support."""
from typing import Dict, Any


# Translations dictionary
TRANSLATIONS = {
    'ru': {
        # Main menu
        'catalog': '🛍 Каталог',
        'balance': '💰 Мой баланс',
        'select_region': '📍 Выбрать регион',
        'purchase_history': '📜 История покупок',
        'help': 'ℹ️ Помощь',
        'price_list': '💵 Прайс-лист',
        'language': '🌐 Язык',
        
        # Welcome message
        'welcome': '👋 Добро пожаловать, {name}!',
        'welcome_text': 'Я бот для покупки цифровых товаров за криптовалюту (SOL).',
        'your_wallet': '🔹 Ваш личный кошелек:',
        'balance_label': '💰 Баланс:',
        'select_region_hint': '📍 Выберите регион и город, чтобы увидеть доступные товары.',
        'use_menu': 'Используйте меню ниже для навигации.',
        'god_mode_available': '👑 Вам доступен GOD режим. Команда: /god',
        
        # Common
        'back': '◀️ Назад',
        'cancel': '❌ Отмена',
        'confirm': '✅ Подтвердить',
        'success': '✅ Успешно!',
        'error': '❌ Ошибка',
    },
    'en': {
        'catalog': '🛍 Catalog',
        'balance': '💰 My Balance',
        'select_region': '📍 Select Region',
        'purchase_history': '📜 Purchase History',
        'help': 'ℹ️ Help',
        'price_list': '💵 Price List',
        'language': '🌐 Language',
        
        'welcome': '👋 Welcome, {name}!',
        'welcome_text': 'I am a bot for buying digital goods with cryptocurrency (SOL).',
        'your_wallet': '🔹 Your personal wallet:',
        'balance_label': '💰 Balance:',
        'select_region_hint': '📍 Select your region and city to see available products.',
        'use_menu': 'Use the menu below for navigation.',
        'god_mode_available': '👑 GOD mode available. Command: /god',
        
        'back': '◀️ Back',
        'cancel': '❌ Cancel',
        'confirm': '✅ Confirm',
        'success': '✅ Success!',
        'error': '❌ Error',
    },
    'lt': {
        'catalog': '🛍 Katalogas',
        'balance': '💰 Mano Balansas',
        'select_region': '📍 Pasirinkti Regioną',
        'purchase_history': '📜 Pirkimų Istorija',
        'help': 'ℹ️ Pagalba',
        'price_list': '💵 Kainų Sąrašas',
        'language': '🌐 Kalba',
        
        'welcome': '👋 Sveiki, {name}!',
        'welcome_text': 'Aš esu botas skaitmeninių prekių pirkimui už kriptovaliutą (SOL).',
        'your_wallet': '🔹 Jūsų asmeninis piniginė:',
        'balance_label': '💰 Balansas:',
        'select_region_hint': '📍 Pasirinkite regioną ir miestą, kad pamatytumėte prieinamas prekes.',
        'use_menu': 'Naudokite meniu navigacijai.',
        'god_mode_available': '👑 GOD režimas prieinamas. Komanda: /god',
        
        'back': '◀️ Atgal',
        'cancel': '❌ Atšaukti',
        'confirm': '✅ Patvirtinti',
        'success': '✅ Sėkmingai!',
        'error': '❌ Klaida',
    },
    'pl': {
        'catalog': '🛍 Katalog',
        'balance': '💰 Moje Saldo',
        'select_region': '📍 Wybierz Region',
        'purchase_history': '📜 Historia Zakupów',
        'help': 'ℹ️ Pomoc',
        'price_list': '💵 Cennik',
        'language': '🌐 Język',
        
        'welcome': '👋 Witaj, {name}!',
        'welcome_text': 'Jestem botem do zakupu towarów cyfrowych za kryptowalutę (SOL).',
        'your_wallet': '🔹 Twój osobisty portfel:',
        'balance_label': '💰 Saldo:',
        'select_region_hint': '📍 Wybierz region i miasto, aby zobaczyć dostępne produkty.',
        'use_menu': 'Użyj menu poniżej do nawigacji.',
        'god_mode_available': '👑 Tryb GOD dostępny. Komenda: /god',
        
        'back': '◀️ Wstecz',
        'cancel': '❌ Anuluj',
        'confirm': '✅ Potwierdź',
        'success': '✅ Sukces!',
        'error': '❌ Błąd',
    },
    'de': {
        'catalog': '🛍 Katalog',
        'balance': '💰 Mein Guthaben',
        'select_region': '📍 Region Wählen',
        'purchase_history': '📜 Kaufhistorie',
        'help': 'ℹ️ Hilfe',
        'price_list': '💵 Preisliste',
        'language': '🌐 Sprache',
        
        'welcome': '👋 Willkommen, {name}!',
        'welcome_text': 'Ich bin ein Bot zum Kauf digitaler Produkte mit Kryptowährung (SOL).',
        'your_wallet': '🔹 Ihre persönliche Wallet:',
        'balance_label': '💰 Guthaben:',
        'select_region_hint': '📍 Wählen Sie Ihre Region und Stadt, um verfügbare Produkte zu sehen.',
        'use_menu': 'Verwenden Sie das Menü unten zur Navigation.',
        'god_mode_available': '👑 GOD-Modus verfügbar. Befehl: /god',
        
        'back': '◀️ Zurück',
        'cancel': '❌ Abbrechen',
        'confirm': '✅ Bestätigen',
        'success': '✅ Erfolg!',
        'error': '❌ Fehler',
    },
    'cs': {
        'catalog': '🛍 Katalog',
        'balance': '💰 Můj Zůstatek',
        'select_region': '📍 Vybrat Region',
        'purchase_history': '📜 Historie Nákupů',
        'help': 'ℹ️ Nápověda',
        'price_list': '💵 Ceník',
        'language': '🌐 Jazyk',
        
        'welcome': '👋 Vítejte, {name}!',
        'welcome_text': 'Jsem bot pro nákup digitálního zboží za kryptoměnu (SOL).',
        'your_wallet': '🔹 Vaše osobní peněženka:',
        'balance_label': '💰 Zůstatek:',
        'select_region_hint': '📍 Vyberte region a město, abyste viděli dostupné produkty.',
        'use_menu': 'Použijte menu níže pro navigaci.',
        'god_mode_available': '👑 GOD režim dostupný. Příkaz: /god',
        
        'back': '◀️ Zpět',
        'cancel': '❌ Zrušit',
        'confirm': '✅ Potvrdit',
        'success': '✅ Úspěch!',
        'error': '❌ Chyba',
    }
}

# Language names
LANGUAGE_NAMES = {
    'ru': '🇷🇺 Русский',
    'en': '🇬🇧 English',
    'lt': '🇱🇹 Lietuvių',
    'pl': '🇵🇱 Polski',
    'de': '🇩🇪 Deutsch',
    'cs': '🇨🇿 Čeština'
}


class LanguageService:
    """Service for managing translations."""
    
    @staticmethod
    def get_text(language: str, key: str, **kwargs) -> str:
        """
        Get translated text.
        
        Args:
            language: Language code (ru, en, lt, pl, de, cs)
            key: Translation key
            **kwargs: Format parameters
            
        Returns:
            Translated text
        """
        # Fallback to Russian if language not found
        lang_dict = TRANSLATIONS.get(language, TRANSLATIONS['ru'])
        
        # Get text, fallback to Russian if key not found
        text = lang_dict.get(key, TRANSLATIONS['ru'].get(key, key))
        
        # Format with parameters if provided
        if kwargs:
            try:
                return text.format(**kwargs)
            except KeyError:
                return text
        
        return text
    
    @staticmethod
    def get_language_name(language: str) -> str:
        """Get language display name."""
        return LANGUAGE_NAMES.get(language, LANGUAGE_NAMES['ru'])
    
    @staticmethod
    def get_all_languages() -> Dict[str, str]:
        """Get all available languages."""
        return LANGUAGE_NAMES.copy()


# Global language service
language_service = LanguageService()

