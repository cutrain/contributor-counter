console.log("111111111111111");
var app = {
  mounted: function (){
    console.log("haha");
    this.calcCurrentPage();
  },
  methods: {
    calcCurrentPage() {
      console.log("calcCurrentPage");
      this.tableData = [];
      let from = (this.currentPage - 1) * this.pageSize;
      let to = this.currentPage * this.pageSize;
      for (let i = from; i < to && i < this.totalNum; ++i)
        this.tableData.push(this.tableDataAll[i]);
    },
    currentChange(currentPage) {
      console.log("currentChange");
      this.currentPage = currentPage;
      this.calcCurrentPage();
    },
    sizeChange(pageSize) {
      console.log("sizeChange");
      this.pageSize = pageSize;
      this.currentChange(1);
    },
    sort_data({column, prop, order}) {
      console.log('sort', prop);
      if (prop == 'uname')
        this.tableDataAll.sort((a, b)=>{
          if (order == 'ascending')
            return a[prop].localeCompare(b[prop]);
          else
            return b[prop].localeCompare(a[prop]);
        });
      else
        this.tableDataAll.sort((a, b)=>{
          if (order == 'ascending')
            return a[prop] - b[prop];
          else
            return b[prop] - a[prop];
        });
      this.currentChange(this.currentPage);
    }
  },
  computed: {
    totalNum() {
      return this.tableDataAll.length;
    }
  },
  data() {
    return {
      pageSize: 10,
      currentPage: 1,
      tableData: [],
      tableDataAll: tableDataAll
    }
  }
};
var Ctor = Vue.extend(app);
new Ctor().$mount('#app');
