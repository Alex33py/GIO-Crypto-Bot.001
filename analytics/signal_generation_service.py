"""
Signal Generation Service
Профессиональный сервис для автоматической и ручной генерации сигналов
"""
import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from datetime import timedelta
from datetime import datetime, timezone
from typing import Optional
import logging

logger = logging.getLogger('gio_bot')


class SignalGenerationService:
    """
    Централизованный сервис для генерации торговых сигналов

    Особенности:
    - Автоматическая генерация по расписанию
    - Ручной триггер через Telegram
    - Детальное логирование причин отказа
    - Адаптивные фильтры
    - Метрики производительности
    """

    def __init__(
        self,
        bot,
        scenario_matcher,
        signal_generator,
        mtf_analyzer,
        risk_calculator,
        signal_recorder,
        telegram_handler=None
    ):
        self.bot = bot
        self.scenario_matcher = scenario_matcher
        self.signal_generator = signal_generator
        self.mtf_analyzer = mtf_analyzer
        self.risk_calculator = risk_calculator
        self.signal_recorder = signal_recorder
        self.telegram_handler = telegram_handler

        # Статистика
        self.stats = {
            'attempts': 0,
            'generated': 0,
            'blocked_by_mtf': 0,
            'blocked_by_cvd': 0,
            'blocked_by_confidence': 0,
            'blocked_by_other': 0
        }
        self._price_cache = {}  # кеш цен: { symbol: (price, timestamp) }
        self._cache_ttl = timedelta(seconds=30)

        logger.info("✅ SignalGenerationService инициализирован")

    async def generate_signals_for_all_symbols(
        self,
        manual_trigger: bool = False
    ) -> Dict[str, any]:

        """
        Генерация сигналов для всех отслеживаемых символов

        Args:
            manual_trigger: True если запущено вручную через Telegram

        Returns:
            Dict с результатами генерации
        """

        start_time = datetime.now()

        trigger_type = "MANUAL" if manual_trigger else "AUTO"

        # ✅ ИСПРАВЛЕНО: Получаем символы из конфига
        from config.settings import TRACKED_SYMBOLS
        tracked_symbols = TRACKED_SYMBOLS

        logger.info(f"🔍 [{trigger_type}] Начинаю проверку сигналов для {len(tracked_symbols)} пар...")

        results = {
            'signals_generated': [],
            'checks_performed': 0,
            'failures': []
        }

        for symbol in tracked_symbols:
            try:
                self.stats['attempts'] += 1
                results['checks_performed'] += 1

                # Получаем MTF данные из кэша бота
                mtf_data = None
                if hasattr(self.bot, 'mtf_cache') and symbol in self.bot.mtf_cache:
                    mtf_data = self.bot.mtf_cache.get(symbol)

                if not mtf_data:
                    failure_reason = f"MTF данные не готовы"
                    logger.debug(f"⏭️ {symbol}: {failure_reason}")
                    results['failures'].append({
                        'symbol': symbol,
                        'reason': failure_reason
                    })
                    self.stats['blocked_by_other'] += 1
                    continue


                # Получить текущую цену
                current_price = await self._get_current_price(symbol)
                if not current_price:
                    failure_reason = f"Цена недоступна"
                    logger.debug(f"⏭️ {symbol}: {failure_reason}")
                    results['failures'].append({
                        'symbol': symbol,
                        'reason': failure_reason
                    })
                    self.stats['blocked_by_other'] += 1
                    continue

                # Подготовить market data
                market_data = self._prepare_market_data(symbol, current_price, mtf_data)
                # Используем расширенный набор индикаторов
                indicators = market_data.get('indicators', {})  # Расширенный набор из _prepare_market_data()

                mtf_trends = {
                    '1H': market_data['mtf'].get('1h', {}).get('trend', 'neutral'),
                    '4H': market_data['mtf'].get('4h', {}).get('trend', 'neutral'),
                    '1D': market_data['mtf'].get('1d', {}).get('trend', 'neutral')
                }
                volume_profile = market_data.get('volume', {})
                news_sentiment = {'score': 0, 'overall_score': 0, 'overall': 'neutral'}
                veto_checks = {}

                scenario_result = self.scenario_matcher.match_scenario(
                    symbol=symbol,
                    market_data=market_data,
                    indicators=indicators,  # ✅ Теперь содержит все расширенные метрики!
                    mtf_trends=mtf_trends,
                    volume_profile=volume_profile,
                    news_sentiment=news_sentiment,
                    veto_checks=veto_checks
                )



                if not scenario_result or not scenario_result.get('matched'):
                    failure_reason = self._extract_failure_reason(scenario_result)
                    logger.debug(f"⏭️ {symbol}: {failure_reason}")
                    results['failures'].append({
                        'symbol': symbol,
                        'reason': failure_reason
                    })
                    self._update_stats_from_failure(failure_reason)
                    continue

                # Сценарий совпал - создать сигнал
                signal = await self._create_signal(
                    symbol=symbol,
                    scenario_result=scenario_result,
                    market_data=market_data,
                    current_price=current_price
                )

                if signal:
                    # Сохранить в БД
                    self.signal_recorder.record_signal(
                    symbol=signal['symbol'],
                    direction=signal['direction'],
                    entry_price=signal['entry_price'],
                    sl_price=signal['stop_loss'],
                    tp1_price=signal['tp1_price'],
                    tp2_price=signal['tp2_price'],
                    tp3_price=signal['tp3_price'],
                    scenario_id=signal['scenario_id'],
                    status=signal['status'],
                    quality_score=signal.get('confidence', 0),
                    risk_reward=signal.get('risk_profile', 0.01),
                    strategy=signal.get('strategy', 'unknown'),
                    market_regime=signal.get('market_regime', 'neutral'),
                    confidence=signal.get('confidence', 'medium'),
                    phase=signal.get('phase', 'unknown'),
                    risk_profile=signal.get('risk_profile', 'moderate'),
                    tactic_name=signal.get('tactic_name', 'default'),
                    validation_score=signal.get('validation_score', 0.0),
                    trigger_score=signal.get('trigger_score', 0.0)
                )

                    logger.info(f"Сигнал сохранен: {signal['id']} | Статус: {signal.get('status', 'unknown')}")

                    # Добавить в результаты
                    results['signals_generated'].append(signal)
                    self.stats['generated'] += 1

                    logger.info(
                        f"✅ [{trigger_type}] НОВЫЙ СИГНАЛ: {symbol} "
                        f"{signal.get('direction')} @ {current_price:.2f} "
                        f"| Scenario: {scenario_result.get('scenario_id')} ")
                       # f"| Confidence: {scenario_result.get('confidence', 0):.1f}%")

                    confidence = scenario_result.get('confidence', 'unknown')
                    if isinstance(confidence, str):
                        confidence_map = {'high': 80, 'medium': 50, 'low': 30}
                        confidence_num = confidence_map.get(confidence, 0)
                    else:
                        confidence_num = confidence

                    logger.info(
                        f"✅ [{trigger_type}] НОВЫЙ СИГНАЛ: {symbol} "
                        f"{signal.get('direction')} @ {current_price:.2f} "
                        f"| Scenario: {scenario_result.get('scenario_id')} "
                        f"| Confidence: {confidence_num:.1f}%"
                    )

                    # Отправить уведомление в Telegram
                    if self.telegram_handler:
                        await self._send_telegram_alert(signal, manual_trigger)

            except Exception as e:
                logger.error(f"❌ Ошибка генерации сигнала для {symbol}: {e}", exc_info=True)
                results['failures'].append({
                    'symbol': symbol,
                    'reason': f"Exception: {str(e)}"
                })

        # Финальная статистика
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info(
            f"📊 [{trigger_type}] Проверка завершена за {elapsed:.1f}s | "
            f"Сгенерировано: {len(results['signals_generated'])} | "
            f"Проверено: {results['checks_performed']} | "
            f"Неудачно: {len(results['failures'])}"
        )

        if manual_trigger and len(results['signals_generated']) == 0:
            logger.info(f"💡 Причины отсутствия сигналов:")
            logger.info(f"   • MTF противоречия: {self.stats['blocked_by_mtf']}")
            logger.info(f"   • Низкий CVD: {self.stats['blocked_by_cvd']}")
            logger.info(f"   • Низкая confidence: {self.stats['blocked_by_confidence']}")
            logger.info(f"   • Другие причины: {self.stats['blocked_by_other']}")

        return results


    async def _get_current_price(self, symbol: str, max_cache_age_seconds: int = 60) -> Optional[float]:
        now = datetime.now(timezone.utc)

        # Проверяем кеш
        if symbol in self._price_cache:
            price, timestamp = self._price_cache[symbol]
            age_seconds = (now - timestamp).total_seconds()
            if age_seconds < self._cache_ttl.total_seconds():
                logger.debug(f"💾 {symbol} цена из кеша (возраст {age_seconds:.1f}s): ${price:.2f}")
                return price
            else:
                logger.debug(f"⚠️ {symbol} кеш устарел ({age_seconds:.1f}s), обновляем...")

        # Если кеш устарел или отсутствует, пробуем получить из MTF cache
        if hasattr(self.bot, 'mtf_cache') and symbol in self.bot.mtf_cache:
            mtf_data = self.bot.mtf_cache.get(symbol, {})
            for tf in ['1h', '4h', '1d']:
                if tf in mtf_data:
                    close_price = mtf_data[tf].get('close')
                    if close_price and close_price > 0:
                        logger.debug(f"⌛️ {symbol} цена из MTF кеша ({tf}): ${close_price:.2f}")
                        self._price_cache[symbol] = (float(close_price), now)
                        return float(close_price)

        # Пробуем получить из Bybit klines cache
        if hasattr(self.bot, 'bybit_connector') and hasattr(self.bot.bybit_connector, 'klines_cache'):
            connector = self.bot.bybit_connector
            for interval_key in [f"{symbol}_60", f"{symbol}_240", f"{symbol}_D"]:
                klines = connector.klines_cache.get(interval_key, [])
                if klines:
                    last_candle = klines[-1]
                    close_price = None
                    if isinstance(last_candle, dict):
                        close_price = last_candle.get('close')
                    elif isinstance(last_candle, (list, tuple)) and len(last_candle) >= 5:
                        close_price = last_candle[4]
                    if close_price and float(close_price) > 0:
                        logger.debug(f"⌛️ {symbol} цена из Bybit klines cache ({interval_key}): ${float(close_price):.2f}")
                        self._price_cache[symbol] = (float(close_price), now)
                        return float(close_price)

        # Если не получили цену в кеше, запрашиваем напрямую у API
        if hasattr(self.bot, 'bybit_connector'):
            connector = self.bot.bybit_connector
            try:
                klines = await connector._get_klines(symbol, '1', limit=1)
                if klines:
                    last_candle = klines[-1]
                    close_price = None
                    if isinstance(last_candle, dict):
                        close_price = last_candle.get('close')
                    elif isinstance(last_candle, (list, tuple)) and len(last_candle) >= 5:
                        close_price = last_candle[4]

                    if close_price and float(close_price) > 0:
                        price = float(close_price)
                        self._price_cache[symbol] = (price, now)
                        logger.debug(f"🌐 {symbol} цена из API обновлена: ${price:.2f}")
                        return price
                    else:
                        logger.warning(f"⚠️ {symbol}: Не удалось извлечь цену из последней свечи.")
                else:
                    logger.warning(f"⚠️ {symbol}: Пустой ответ от _get_klines API.")
            except Exception as e:
                logger.error(f"❌ {symbol}: Ошибка получения цены с API: {e}", exc_info=True)

        logger.warning(f"⚠️ {symbol}: Не удалось получить актуальную цену из кеша и API.")
        return None






    def _prepare_market_data(self, symbol: str, current_price: float, mtf_data: Dict) -> Dict:
        """
        Подготовить расширенный market data для сценария

        Включает:
        - MTF индикаторы (adx_1h, rsi_1h, ema_20_1h, etc)
        - ATR метрики
        - Volume analytics
        - Mock данные для отсутствующих источников
        """

        # ✅ ДОБАВЛЕНО: Получаем свечи для regime detector
        candles = []

        # Попытка 1: Из MTF cache (приоритет)
        if hasattr(self.bot, 'mtf_cache') and symbol in self.bot.mtf_cache:
            mtf_symbol_data = self.bot.mtf_cache.get(symbol, {})

            # Пробуем получить из разных таймфреймов
            for interval in ['1h', '4h', '1d']:
                if interval in mtf_symbol_data:
                    interval_data = mtf_symbol_data[interval]

                    # Если есть готовый список свечей
                    if 'candles' in interval_data and interval_data['candles']:
                        candles = interval_data['candles']
                        logger.debug(f"📊 {symbol}: Получено {len(candles)} свечей из MTF cache ({interval})")
                        break

        # Попытка 2: Из Bybit klines cache
        if not candles and hasattr(self.bot, 'bybit_connector'):
            connector = self.bot.bybit_connector

            if hasattr(connector, 'klines_cache'):
                # Пробуем разные интервалы
                for interval_key in [f"{symbol}_60", f"{symbol}_240", f"{symbol}_D"]:
                    klines = connector.klines_cache.get(interval_key, [])

                    if klines and len(klines) > 0:
                        candles = klines
                        logger.debug(f"📊 {symbol}: Получено {len(candles)} свечей из Bybit klines cache")
                        break

        # Если свечей все равно нет - логируем предупреждение
        if not candles:
            logger.warning(f"⚠️ {symbol}: Свечи не найдены! Market Regime Detector не сможет работать.")

        # ===== РАСШИРЕННЫЙ НАБОР ИНДИКАТОРОВ =====

        # 1. Базовые MTF данные (уже есть)
        indicators_1h = mtf_data.get('1h', {})
        indicators_4h = mtf_data.get('4h', {})
        indicators_1d = mtf_data.get('1d', {})

        # 2. MTF индикаторы для сценариев
        extended_indicators = {}

        # ADX для разных таймфреймов
        extended_indicators['adx'] = indicators_1h.get('adx', 0)
        extended_indicators['adx_1h'] = indicators_1h.get('adx', 0)
        extended_indicators['adx_4h'] = indicators_4h.get('adx', 0)
        extended_indicators['adx_slope'] = 0  # TODO: рассчитать наклон ADX

        # RSI для разных таймфреймов
        extended_indicators['rsi'] = indicators_1h.get('rsi', 50)
        extended_indicators['rsi_1h'] = indicators_1h.get('rsi', 50)
        extended_indicators['rsi_4h'] = indicators_4h.get('rsi', 50)

        # EMA для разных таймфреймов
        extended_indicators['ema_20'] = indicators_1h.get('ema_20', current_price)
        extended_indicators['ema_50'] = indicators_1h.get('ema_50', current_price)
        extended_indicators['ema_20_1h'] = indicators_1h.get('ema_20', current_price)
        extended_indicators['ema_50_1h'] = indicators_1h.get('ema_50', current_price)

        # MACD
        extended_indicators['macd'] = indicators_1h.get('macd', 0)
        extended_indicators['macd_signal'] = indicators_1h.get('macd_signal', 0)
        extended_indicators['macd_hist'] = indicators_1h.get('macd_hist', 0)
        extended_indicators['macd_hist_1h'] = indicators_1h.get('macd_hist', 0)

        # 3. ATR метрики
        atr_value = indicators_1h.get('atr_14', current_price * 0.02)
        extended_indicators['atr'] = atr_value
        extended_indicators['atr_14'] = atr_value
        extended_indicators['atr_ma20'] = indicators_1h.get('atr_sma_20', atr_value)
        extended_indicators['atr_sma_20'] = indicators_1h.get('atr_sma_20', atr_value)
        extended_indicators['atr_pct'] = (atr_value / current_price) * 100 if current_price > 0 else 0

        # 4. Volume метрики
        current_volume = indicators_1h.get('volume', 0)
        volume_ma20 = indicators_1h.get('volume_avg', current_volume if current_volume > 0 else 1)

        extended_indicators['volume'] = current_volume
        extended_indicators['volume_ma20'] = volume_ma20
        extended_indicators['volume_avg'] = volume_ma20
        extended_indicators['avg_volume'] = volume_ma20
        extended_indicators['volume_delta_1h'] = ((current_volume / volume_ma20) - 1) * 100 if volume_ma20 > 0 else 0

        # 5. Price метрики
        extended_indicators['price'] = current_price
        extended_indicators['close'] = current_price
        extended_indicators['open'] = indicators_1h.get('open', current_price)
        extended_indicators['high'] = indicators_1h.get('high', current_price)
        extended_indicators['low'] = indicators_1h.get('low', current_price)

        # 6. Trend метрики
        extended_indicators['trend'] = indicators_1h.get('trend', 'neutral')
        extended_indicators['strength'] = indicators_1h.get('strength', 0)

        # 7. Volume Profile
        volume_profile_data = self._get_volume_data(symbol)
        extended_indicators['poc'] = current_price  # Point of Control
        extended_indicators['vah'] = current_price * 1.01  # Value Area High
        extended_indicators['val'] = current_price * 0.99  # Value Area Low
        extended_indicators['vwap'] = current_price  # VWAP

        # 8. ===== MOCK ДАННЫЕ для отсутствующих источников =====

        # Funding Rate (TODO: интеграция с exchange API)
        extended_indicators['funding_rate_bp'] = 0  # basis points
        extended_indicators['funding_trend_24h'] = 'neutral'

        # Open Interest (TODO: интеграция с exchange API)
        extended_indicators['open_interest_delta_pct'] = 0
        extended_indicators['oi_24h_change'] = 0

        # Long/Short Ratio (TODO: интеграция с exchange API)
        extended_indicators['long_short_ratio'] = 1.0
        extended_indicators['crowding_index'] = 0.5

        # CVD / Delta - СИНХРОННЫЙ расчёт
        cvd_data = self._get_cvd_data(symbol)
        cvd_value = cvd_data.get('value', 0) if cvd_data else 0

        extended_indicators['cvd_slope'] = 0
        extended_indicators['delta_5m_avg'] = float(cvd_value) if cvd_value else 0.0

        # Cluster Analysis (TODO: интеграция cluster analyzer)
        extended_indicators['cluster_stacked_imbalance_up'] = 0
        extended_indicators['cluster_imbalance'] = 0

        # Score (placeholder)
        extended_indicators['score'] = 0.5

        logger.debug(f"📊 {symbol}: Подготовлено {len(extended_indicators)} расширенных метрик")

        return {
            'symbol': symbol,
            'price': current_price,
            'timestamp': datetime.now().isoformat(),
            'mtf': mtf_data,
            'candles': candles,
            'indicators': extended_indicators,  # ✅ ДОБАВЛЕНО: расширенный набор
            'orderbook': self._get_orderbook_data(symbol),
            'volume': volume_profile_data,
            'cvd': cvd_data
        }



    def _get_orderbook_data(self, symbol: str) -> Dict:
        """Получить данные orderbook для символа"""
        try:
            if hasattr(self.bot, 'orderbook_analyzer'):
                return self.bot.orderbook_analyzer.get_summary(symbol)
            return {}
        except:
            return {}

    def _get_volume_data(self, symbol: str) -> Dict:
        """Получить данные объёма"""
        try:
            # Получаем из кэша бота
            if hasattr(self.bot, 'mtf_cache') and symbol in self.bot.mtf_cache:
                mtf_data = self.bot.mtf_cache.get(symbol)
                if mtf_data and '1h' in mtf_data:
                    return {
                        'current': mtf_data['1h'].get('volume', 0),
                        'avg_20': mtf_data['1h'].get('volume_avg', 0)
                    }
            return {}
        except:
            return {}


    def _get_cvd_data(self, symbol: str) -> Dict:
        """Получить CVD данные (синхронно)"""
        try:
            if hasattr(self.bot, 'orderbook_analyzer'):
                cvd = self.bot.orderbook_analyzer.get_cvd(symbol)

                # ✅ ПРОВЕРКА: Если вернулся coroutine - возвращаем 0
                if hasattr(cvd, '__await__'):
                    logger.debug(f"⚠️ {symbol}: CVD async, используем 0")
                    return {'value': 0}

                return {'value': cvd} if cvd else {}
            return {}
        except Exception as e:
            logger.debug(f"⚠️ {symbol}: CVD error: {e}")
            return {}


    async def _create_signal(
        self,
        symbol: str,
        scenario_result: Dict,
        market_data: Dict,
        current_price: float
    ) -> Optional[Dict]:
        """Создать торговый сигнал"""
        try:
            # ✅ ИСПРАВЛЕНО: Используем уровни из scenario_result напрямую
            # scenario_result уже содержит stop_loss, tp1_price, tp2_price, tp3_price из unified_scenario_matcher

            signal = {
                'id': self._generate_signal_id(),
                'symbol': symbol,
                'direction': scenario_result.get('direction', 'LONG'),
                'entry_price': current_price,
                'stop_loss': scenario_result.get('stop_loss'),
                'take_profit': scenario_result.get('tp1_price'),  # Основной TP
                'tp1_price': scenario_result.get('tp1_price'),
                'tp2_price': scenario_result.get('tp2_price'),
                'tp3_price': scenario_result.get('tp3_price'),
                'scenario_id': scenario_result.get('scenario_id'),
                'confidence': scenario_result.get('confidence', 0),
                'timestamp': datetime.now().isoformat(),
                'status': 'PENDING',
                'mtf_alignment': self._get_mtf_summary(market_data['mtf'])
            }

            return signal

        except Exception as e:
            logger.error(f"❌ Ошибка создания сигнала: {e}", exc_info=True)
            return None


    def _generate_signal_id(self) -> int:
        """Генерация уникального ID сигнала"""
        # Получить последний ID из БД и инкрементировать
        try:
            last_id = self.signal_recorder.get_last_signal_id()
            return last_id + 1 if last_id else 1
        except:
            return int(datetime.now().timestamp())

    def _get_mtf_summary(self, mtf_data: Dict) -> str:
        """Получить краткое описание MTF"""
        try:
            summary = []
            for tf in ['1h', '4h', '1d']:
                if tf in mtf_data:
                    trend = mtf_data[tf].get('trend', 'neutral')
                    strength = mtf_data[tf].get('strength', 0)
                    summary.append(f"{tf}:{trend}({strength:.2f})")
            return " | ".join(summary)
        except:
            return "N/A"

    async def _send_telegram_alert(self, signal: Dict, manual: bool):
        """Отправить уведомление о сигнале в Telegram"""
        try:
            # Конвертируем confidence для отображения
            confidence = signal.get('confidence', 'unknown')
            if isinstance(confidence, str):
                confidence_text = confidence.upper()
            else:
                confidence_text = f"{confidence:.1f}%"

            scenario_id = signal['scenario_id'].replace('_', '\\_')
            alert_text = (
                f"{'🔔 [MANUAL]' if manual else '🎯 [AUTO]'} НОВЫЙ СИГНАЛ\n\n"
                f"{'🟢' if signal['direction'] == 'LONG' else '🔴'} "
                f"#{signal['id']} {signal['symbol']} {signal['direction']}\n"
                f"💰 Entry: ${signal['entry_price']:.2f}\n"
                f"🎯 TP: ${signal.get('take_profit', 'N/A')}\n"
                f"🛑 SL: ${signal.get('stop_loss', 'N/A')}\n"
                f"📊 Confidence: {confidence_text}\n"
                 f"📈 Scenario: {scenario_id}\n"
                f"⏰ {signal['timestamp']}"
            )

            await self.telegram_handler.send_message(alert_text)

        except Exception as e:
            logger.error(f"Ошибка отправки Telegram уведомления: {e}")

    def _extract_failure_reason(self, scenario_result: Optional[Dict]) -> str:
        """Извлечь причину неудачи из результата сценария"""
        if not scenario_result:
            return "Сценарий не вернул результат"

        if not scenario_result.get('matched'):
            # Анализируем почему не совпало
            confidence = scenario_result.get('confidence', 0)
            if confidence < 35:
                return f"Низкая confidence ({confidence:.1f}% < 35%)"

            filters = scenario_result.get('filters', {})
            if not filters.get('mtf_passed'):
                return "MTF фильтр не пройден (противоречивые тренды)"

            if not filters.get('cvd_passed'):
                cvd = filters.get('cvd_value', 0)
                return f"CVD недостаточен ({cvd:.2f}% < 0.15%)"

            return "Условия сценария не выполнены"

        return "Неизвестная причина"

    def _update_stats_from_failure(self, reason: str):
        """Обновить статистику на основе причины неудачи"""
        reason_lower = reason.lower()

        if 'mtf' in reason_lower or 'тренд' in reason_lower:
            self.stats['blocked_by_mtf'] += 1
        elif 'cvd' in reason_lower:
            self.stats['blocked_by_cvd'] += 1
        elif 'confidence' in reason_lower or 'уверенность' in reason_lower:
            self.stats['blocked_by_confidence'] += 1
        else:
            self.stats['blocked_by_other'] += 1

    def get_stats(self) -> Dict:
        """Получить статистику работы сервиса"""
        total = self.stats['attempts']
        if total == 0:
            return self.stats

        return {
            **self.stats,
            'success_rate': (self.stats['generated'] / total * 100) if total > 0 else 0,
            'mtf_block_rate': (self.stats['blocked_by_mtf'] / total * 100) if total > 0 else 0,
            'cvd_block_rate': (self.stats['blocked_by_cvd'] / total * 100) if total > 0 else 0
        }

    def reset_stats(self):
        """Сбросить статистику"""
        for key in self.stats:
            self.stats[key] = 0
        logger.info("📊 Статистика SignalGenerationService сброшена")
