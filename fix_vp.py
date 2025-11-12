"""
Патч для добавления метода calculate_from_orderbook
в EnhancedVolumeProfileCalculator
"""

file_path = "analytics/volume_profile.py"

# Читаем файл
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Проверяем есть ли уже метод
if 'def calculate_from_orderbook' in content:
    print("✅ Метод calculate_from_orderbook уже существует!")
    print("   Ничего делать не нужно.")
else:
    print("❌ Метод calculate_from_orderbook отсутствует")
    print("🔧 Добавляю метод...\n")
    
    # Метод для добавления
    new_method = '''
    async def calculate_from_orderbook(self, symbol: str, orderbook: dict, 
                                      timeframe: str = "1h") -> dict:
        """
        Рассчитать Volume Profile из orderbook данных
        
        Args:
            symbol: торговая пара
            orderbook: данные orderbook {'bids': [...], 'asks': [...]}
            timeframe: таймфрейм (по умолчанию 1h)
            
        Returns:
            dict с POC, VAH, VAL и другими метриками
        """
        try:
            # Извлекаем bids и asks
            bids = orderbook.get('bids', [])
            asks = orderbook.get('asks', [])
            
            if not bids or not asks:
                return self._default_vp_result()
            
            # Рассчитываем уровни цен и объёмы
            all_levels = []
            
            # Обрабатываем bids (покупки)
            for price, volume in bids:
                all_levels.append({
                    'price': float(price),
                    'volume': float(volume),
                    'side': 'buy'
                })
            
            # Обрабатываем asks (продажи)
            for price, volume in asks:
                all_levels.append({
                    'price': float(price),
                    'volume': float(volume),
                    'side': 'sell'
                })
            
            # Сортируем по цене
            all_levels.sort(key=lambda x: x['price'])
            
            if not all_levels:
                return self._default_vp_result()
            
            # Находим POC (точка с максимальным объёмом)
            max_volume = 0
            poc_price = all_levels[0]['price']
            
            for level in all_levels:
                if level['volume'] > max_volume:
                    max_volume = level['volume']
                    poc_price = level['price']
            
            # Рассчитываем общий объём
            total_volume = sum(l['volume'] for l in all_levels)
            
            # Находим 70% зону (Value Area)
            target_volume = total_volume * 0.7
            cumulative_volume = 0
            value_area = []
            
            # Начинаем от POC и расширяемся
            sorted_levels = sorted(all_levels, 
                                 key=lambda x: abs(x['price'] - poc_price))
            
            for level in sorted_levels:
                cumulative_volume += level['volume']
                value_area.append(level)
                if cumulative_volume >= target_volume:
                    break
            
            # VAH и VAL
            prices = [l['price'] for l in value_area]
            vah = max(prices) if prices else poc_price
            val = min(prices) if prices else poc_price
            
            return {
                'poc': poc_price,
                'vah': vah,
                'val': val,
                'total_volume': total_volume,
                'value_area_volume': cumulative_volume,
                'levels': len(all_levels),
                'timestamp': orderbook.get('timestamp', None)
            }
            
        except Exception as e:
            self.logger.error(f"❌ calculate_from_orderbook error: {e}")
            return self._default_vp_result()
    
    def _default_vp_result(self) -> dict:
        """Возвращает дефолтный результат Volume Profile"""
        return {
            'poc': 0.0,
            'vah': 0.0,
            'val': 0.0,
            'total_volume': 0.0,
            'value_area_volume': 0.0,
            'levels': 0,
            'timestamp': None
        }
'''
    
    # Находим конец класса EnhancedVolumeProfileCalculator
    lines = content.split('\n')
    insert_index = -1
    
    # Ищем класс
    for i, line in enumerate(lines):
        if 'class EnhancedVolumeProfileCalculator' in line:
            # Ищем конец класса (следующий class или конец файла)
            class_indent = len(line) - len(line.lstrip())
            
            for j in range(i + 1, len(lines)):
                stripped = lines[j].strip()
                
                # Пропускаем пустые строки и комментарии
                if not stripped or stripped.startswith('#'):
                    continue
                
                # Если нашли следующий class или функцию на том же уровне
                current_indent = len(lines[j]) - len(lines[j].lstrip())
                if current_indent <= class_indent and stripped:
                    insert_index = j
                    break
            
            # Если не нашли следующий class, вставляем в конец
            if insert_index == -1:
                insert_index = len(lines)
            
            break
    
    if insert_index > 0:
        # Вставляем новый метод
        lines.insert(insert_index, new_method)
        
        # Записываем обратно
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        print("✅ Метод calculate_from_orderbook добавлен!")
        print(f"✅ Файл {file_path} обновлён!")
        print("\n🎯 ТЕПЕРЬ ПЕРЕЗАПУСТИ БОТА!")
    else:
        print("❌ Не удалось найти класс EnhancedVolumeProfileCalculator")

print("\n" + "="*60)
print("ГОТОВО!")
print("="*60)
