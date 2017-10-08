require "fileutils"
require "open-uri"
require "nokogiri"
require "selenium-webdriver"
require "csv"


def fetch_htmldoc_from(url)
    charset = nil
    html = nil
    html = open(url) do |f|
        charset = f.charset
        f.read
    end
    doc = Nokogiri::HTML.parse(html, nil, charset)
    sleep 1
    return doc
end


def fetch_userid(community_id)
    # userのurlを集める
    p "fetching user id @community #{community_id}"
    user_id_list = []
    pages = get_maxpages(fetch_htmldoc_from("https://bookmeter.com/communities/#{community_id}/members?page=1"))

    1.upto(pages) do |page|
        p "#{page}/#{pages}"
        user_doc = fetch_htmldoc_from("https://bookmeter.com/communities/#{community_id}/members?page=#{page}")
        user_doc.xpath('//a[../@class="item__username"]').each do |a|
            user_id = a[:href].split("/")[2]
            user_id_list.push(user_id)
        end
    end
    return user_id_list
end

def get_maxpages(doc)
    elements = doc.xpath("//*[@class=\"bm-pagination__link\"]")
    if elements.empty?
        return 1
    end
    maxpage = elements[-1][:href].split("=")[-1].to_i
    return maxpage
end

def fetch_userdata(user_id, data, page, max_page)
    url = "https://bookmeter.com/users/#{user_id}/books/read?page=#{page}"
    p url
    doc = fetch_htmldoc_from(url)
    ['title', "authors"].each do |key|
        doc.xpath("//*[@class=\"detail__#{key}\"]").each do |div|
            data[key].push(div.text)
        end
    end

    if page == 1
        max_page = get_maxpages(doc)
    end

    if page >= max_page
        return data
    else
        page += 1
        return fetch_userdata(user_id, data, page, max_page)
    end
end

def write_data(user_id, user_data)
    user_data.each do |d|
    header = d[0]
    data = d[1]

    filename = "#{header}_#{user_id}"
    File.open("data/#{filename}.txt", "w") do |f|
        f.puts data.join("\t")
    end
  end
end

def fetch_htmldoc_bybrowser(url)
    charset = nil
    html = nil
    driver = Selenium::WebDriver.for(:firefox)
    driver.navigate.to(url)

    html = open(url) do |f|
        charset = f.charset
        f.read
    end
    doc = Nokogiri::HTML.parse(driver.page_source, nil, charset)
    driver.quit
    return doc
end

def get_community_id()
    doc = fetch_htmldoc_bybrowser("https://bookmeter.com/communities?filter=none&sort=member_count")
    cid = []
    doc.xpath('//a[../../@class="communities list"]').each do |a|
        cid.push(a[:href].split("/")[-1].to_i)
    end
    return cid
end


def main()
    # cid_list = get_community_id()
    # user_id_list = []
    # cid_list.each do |cid|
    #     user_id_list.concat(fetch_userid(cid))
    # end
    # p user_id_list
    #
    # File.open("data/user_id_raw.txt", "w") do |f|
    #     f.puts user_id_list.join("\t")
    # end
    # data = []

    csv = CSV::read("data/user_id.csv", headers: true)

    done_user_list = []

    Dir.foreach("data/") do |f|
        if f.include? "author"
            uid = f.split("_")[1].split(".")[0]
            done_user_list.push(uid)
        end
    end
    p done_user_list

    csv.reverse_each do |data|
        user_id = data["user_id"]
        if done_user_list.include? user_id
            p "#{data} already exists."
            next
        end
        data_i = {
        "authors" => [],
        "title" => [],
        }
        p "start fetch user_id:#{data}"
        data_i = fetch_userdata(user_id, data_i, 1, 1)
        data.push({
          "data" => data_i,
          "user_id" => user_id
        })
        write_data(user_id, data_i)
    end
end



path = "./data/raw"
FileUtils.mkdir_p(path) unless FileTest.exist?(path)

main
