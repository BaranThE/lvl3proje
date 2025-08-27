import discord
from discord.ext import commands
from logic import DB_Manager
from config import DATABASE, TOKEN

# Discord botu için gerekli izinleri tanımlıyoruz
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

# Botu oluşturuyoruz, komut öneki "!" olacak
bot = commands.Bot(command_prefix='!', intents=intents)

# Veritabanı yöneticisini başlatıyoruz
manager = DB_Manager(DATABASE)

# Bot başarılı şekilde çalışmaya başladığında çalışan olay
@bot.event
async def on_ready():
    print(f'Bot hazır! {bot.user} olarak giriş yapıldı.')

# Başlangıç komutu (!start)
@bot.command(name='start')
async def start_command(ctx):
    await ctx.send("Merhaba! Ben bir proje yöneticisi botuyum.\nProjelerinizi ve onlara dair tüm bilgileri saklamanıza yardımcı olacağım! =)")
    await info(ctx)  # Kullanıcıya bilgi komutunu da gösterir

# Kullanılabilir komutların listesini gösterir (!info)
@bot.command(name='info')
async def info(ctx):
    await ctx.send("""
Kullanabileceğiniz komutlar şunlardır:

!new_project - yeni bir proje eklemek
!projects - tüm projelerinizi listelemek
!update_projects - proje verilerini güncellemek
!skills - belirli bir projeye beceri eklemek
!delete - bir projeyi silmek

Ayrıca, proje adını yazarak projeyle ilgili tüm bilgilere göz atabilirsiniz!""")

# Yeni proje eklemek için kullanılan komut (!new_project)
@bot.command(name='new_project')
async def new_project(ctx):
    await ctx.send("Lütfen projenin adını girin!")

    # Kullanıcının doğru kanalda ve kendisi tarafından mesaj atıldığını kontrol eder
    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel

    # Proje adı alınıyor
    name = await bot.wait_for('message', check=check)
    data = [ctx.author.id, name.content]

    # Proje bağlantısı alınıyor
    await ctx.send("Lütfen projeye ait bağlantıyı gönderin!")
    link = await bot.wait_for('message', check=check)
    data.append(link.content)

    # Kullanıcıya proje durum seçenekleri gösteriliyor
    statuses = [x[0] for x in manager.get_statuses()]
    await ctx.send("Lütfen projenin mevcut durumunu girin!", delete_after=60.0)
    await ctx.send("\n".join(statuses), delete_after=60.0)
    
    # Kullanıcının girdiği durum kontrol ediliyor
    status = await bot.wait_for('message', check=check)
    if status.content not in statuses:
        await ctx.send("Seçtiğiniz durum listede bulunmuyor. Lütfen tekrar deneyin!", delete_after=60.0)
        return

    # Proje kaydediliyor
    status_id = manager.get_status_id(status.content)
    data.append(status_id)
    manager.insert_project([tuple(data)])
    await ctx.send("Proje kaydedildi")

# Kullanıcının projelerini listeleyen komut (!projects)
@bot.command(name='projects')
async def get_projects(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"Project name: {x[2]} \nLink: {x[4]}\n" for x in projects])
        await ctx.send(text)
    else:
        await ctx.send('Henüz herhangi bir projeniz yok!\nBir tane eklemeyi düşünün! !new_project komutunu kullanabilirsiniz.')

# Projelere beceri ekleyen komut (!skills)
@bot.command(name='skills')
async def skills(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        # Kullanıcının sahip olduğu projeler listeleniyor
        projects = [x[2] for x in projects]
        await ctx.send('Bir beceri eklemek istediğiniz projeyi seçin')
        await ctx.send("\n".join(projects))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        project_name = await bot.wait_for('message', check=check)
        if project_name.content not in projects:
            await ctx.send('Bu projeye sahip değilsiniz, lütfen tekrar deneyin!')
            return

        # Kullanıcıya beceri seçenekleri gösteriliyor
        skills = [x[1] for x in manager.get_skills()]
        await ctx.send('Bir beceri seçin')
        await ctx.send("\n".join(skills))

        skill = await bot.wait_for('message', check=check)
        if skill.content not in skills:
            await ctx.send('Görünüşe göre seçtiğiniz beceri listede yok! Lütfen tekrar deneyin!')
            return

        # Beceri veritabanına ekleniyor
        manager.insert_skill(user_id, project_name.content, skill.content)
        await ctx.send(f'{skill.content} becerisi {project_name.content} projesine eklendi')
    else:
        await ctx.send('Henüz herhangi bir projeniz yok!\nBir tane eklemeyi düşünün! !new_project komutunu kullanabilirsiniz.')

# Proje silmek için kullanılan komut (!delete)
@bot.command(name='delete')
async def delete_project(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        await ctx.send("Silmek istediğiniz projeyi seçin")
        await ctx.send("\n".join(projects))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        project_name = await bot.wait_for('message', check=check)
        if project_name.content not in projects:
            await ctx.send('Bu projeye sahip değilsiniz, lütfen tekrar deneyin!')
            return

        # Proje veritabanından siliniyor
        project_id = manager.get_project_id(project_name.content, user_id)
        manager.delete_project(user_id, project_id)
        await ctx.send(f'{project_name.content} projesi veri tabanından silindi!')
    else:
        await ctx.send('Henüz herhangi bir projeniz yok!\nBir tane eklemeyi düşünün! !new_project komutunu kullanabilirsiniz.')

# Projeleri güncellemek için kullanılan komut (!update_projects)
@bot.command(name='update_projects')
async def update_projects(ctx):
    user_id = ctx.author.id
    projects = manager.get_projects(user_id)
    if projects:
        projects = [x[2] for x in projects]
        await ctx.send("Güncellemek istediğiniz projeyi seçin")
        await ctx.send("\n".join(projects))

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        project_name = await bot.wait_for('message', check=check)
        if project_name.content not in projects:
            await ctx.send("Bir hata oldu! Lütfen güncellemek istediğiniz projeyi tekrar seçin:")
            return

        # Kullanıcıya değiştirilebilecek alanlar gösteriliyor
        await ctx.send("Projede neyi değiştirmek istersiniz?")
        attributes = {'Proje adı': 'project_name', 'Açıklama': 'description', 'Proje bağlantısı': 'url', 'Proje durumu': 'status_id'}
        await ctx.send("\n".join(attributes.keys()))

        attribute = await bot.wait_for('message', check=check)
        if attribute.content not in attributes:
            await ctx.send("Hata oluştu! Lütfen tekrar deneyin!")
            return

        # Eğer güncellenmek istenen şey proje durumu ise
        if attribute.content == 'Durum':
            statuses = manager.get_statuses()
            await ctx.send("Projeniz için yeni bir durum seçin")
            await ctx.send("\n".join([x[0] for x in statuses]))
            update_info = await bot.wait_for('message', check=check)
            if update_info.content not in [x[0] for x in statuses]:
                await ctx.send("Yanlış durum seçildi, lütfen tekrar deneyin!")
                return
            update_info = manager.get_status_id(update_info.content)
        else:
            # Yeni değer istenir
            await ctx.send(f"{attribute.content} için yeni bir değer girin")
            update_info = await bot.wait_for('message', check=check)
            update_info = update_info.content

        # Güncelleme işlemi yapılır
        manager.update_projects(attributes[attribute.content], (update_info, project_name.content, user_id))
        await ctx.send("Tüm işlemler tamamlandı! Proje güncellendi!")
    else:
        await ctx.send('Henüz herhangi bir projeniz yok!\nBir tane eklemeyi düşünün! !new_project komutunu kullanabilirsiniz.')

# Botu çalıştırıyoruz
bot.run(TOKEN)
