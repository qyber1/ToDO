from aiogram import types, Router
from aiogram.filters import Command



from aiogram.fsm.context import FSMContext
from handlers.state import FSMHandler

from sqlalchemy.orm import sessionmaker

from db.requests import get_user, new_user, add_action, delete_actions, show_action, check_action, delete_action, get_all_action

router = Router()


@router.message(Command(commands=['start']))
async def commands_start(message: types.Message, db_pool: sessionmaker):
    user = await get_user(db_pool, message.from_user.id)
    if user:
        await message.answer(f'<code>Привет, {message.from_user.username}</code>', parse_mode='HTML')
    else:
        await new_user(db_pool, message.from_user.id)
        await message.answer(f"<code>Добро пожаловать, {message.from_user.username}</code>", parse_mode='HTML')


@router.message(Command(commands=['add']))
async def addtask(message: types.Message, state: FSMContext):
    '''Функция для перехода к функции добавления задач через состояние и команду add'''
    await state.set_state(FSMHandler.add_task)
    await message.answer('<code>Введите задачи на сегодня для добавления.\nДля остановки введите слово "стоп"</code>',
                         parse_mode='HTML')


@router.message(FSMHandler.add_task)
async def echo(message: types.Message, state: FSMContext, db_pool: sessionmaker):
    '''Функция для добавления задач на день. Если в условии есть слово "стоп" то выходит из функции,иначе повторный вызов функции'''
    if message.text.lower() == 'стоп':
        await state.clear()
        await message.answer(f'<code>Задачи добавлены.\nВведите </code> /show <code> чтобы показать список дел </code>',
                             parse_mode='HTML')
    else:
        await add_action(db_pool, message.text, message.from_user.id)
        await message.answer('<code>Задача добавлена.\nВведи следующую...</code>', parse_mode='HTML')
        return echo


@router.message(Command(commands=['delete']))
async def deletetask(message: types.Message, state: FSMContext, db_pool: sessionmaker):
    '''Функция для перехода к функции удалению задач через состояние и команду delete'''
    action = await delete_actions(db_pool, message.from_user.id)
    if action:
        await state.set_state(FSMHandler.delete_task)
        await message.answer(
            '<code>Введите выполненную задачу для удаления. \nДля остановки введите слово "стоп"</code>',
            parse_mode='HTML')
    else:
        await message.answer('<code>Нет задач. Для добавления нажмите</code> /add', parse_mode='HTML')


@router.message(FSMHandler.delete_task)
async def edit(message: types.Message, state: FSMContext, db_pool: sessionmaker):
    '''Функция для редактирования задач'''
    if message.text.lower() == 'стоп':
        await state.clear()
        await message.answer(f'<code>Задачи отредактированы.</code>', parse_mode='HTML')

    else:
        action = await check_action(db_pool, message.text.lower(), message.from_user.id)
        if isinstance(action, str):
            await delete_action(db_pool, action, message.from_user.id)
            action = await get_all_action(db_pool, message.from_user.id)
            if isinstance(action, str):
                await message.answer('<code>Задача удалена!\nВведи следующую...</code>', parse_mode='HTML')
                return edit
            else:
                await state.clear()
                await message.answer('<code>Задач больше нет. Поздравляю!</code>', parse_mode='HTML')
        elif isinstance(action, type(None)):
            await message.answer('<code>Такой задачи нет в списке. Введите ещё раз...</code>',
                                         parse_mode='HTML')
            return edit


@router.message(Command(commands=['show']))
async def show_task(message: types.Message, db_pool: sessionmaker):
    '''Функия для показа текущих дел.'''
    list_action = []
    actions = await show_action(db_pool, message.from_user.id)
    print(actions)
    for action in actions:
        list_action.append(action[0])
        output_action = '\n'.join(list_action)
    if list_action:
        await message.answer(f'<code>Твои задачи на день:</code> \n\n{output_action}', parse_mode='HTML')
    else:
        await message.answer(f'<code>Задач нет!</code>', parse_mode='HTML')


@router.message(Command(commands=['help']))
async def help(message: types.Message):
    await message.answer(
        "<code>Этот бот помогает добавлять и уследить за своими задачами на день. Таким образом вы будете более эффективными\n\n"
        "Для того, чтобы добавить задачу - нажмите</code> /add <code>\n\n"
        "Для того, чтобы удалить выполненную задачу - нажмите</code> /delete <code>\n\n"
        "Для того, чтобы показать список текущих дел - нажмите </code> /show <code>\n\n"
        "Спасибо Андрюхе за помощь в разработке</code>", parse_mode='HTML')


@router.message()
async def repeat_msg(message: types.Message):
    '''Функция повторюшка, если чел не ввел команду'''
    await message.answer(f'Ты написал - {message.text}.\n Я не понимаю, что нужно делать.\n Введи /help',
                         parse_mode='HTML')
